from datetime import date

import pytest

from ....accounts.services.model_services import AccountBalanceModelService
from ....accounts.tests.factories import AccountFactory
from ....bookkeeping import balance_sources
from ....core.tests.utils import count_queries
from ...models import Expense, ExpenseKeyword
from ...receipts.reader import ReceiptReader
from ...receipts.receipt import ReceiptLine
from ...services.receipt_import import (
    ExpenseGroup,
    ExpenseGroups,
    ReceiptImport,
    ReviewedLine,
    ShopMoney,
)
from ..factories import ExpenseKeywordFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..receipts.pdfs import FIXTURES

pytestmark = pytest.mark.django_db

IMPORT_DATE = date(2026, 1, 1)


@pytest.fixture
def journal(main_user):
    return main_user.journal


@pytest.fixture
def account(journal):
    return AccountFactory(journal=journal)


@pytest.fixture
def expense_type(journal):
    return ExpenseTypeFactory(title="Maistas", journal=journal)


@pytest.fixture
def first_name(expense_type):
    return ExpenseNameFactory(title="Sena", parent=expense_type)


@pytest.fixture
def last_name(expense_type):
    return ExpenseNameFactory(title="Nauja", parent=expense_type)


def _line(title="Prekė", amount=1, price=100, is_deposit=False):
    return ReceiptLine(title=title, amount=amount, price=price, is_deposit=is_deposit)


def _review(line, name, *, keyword="prekė", carries_shop_money=False):
    return ReviewedLine(
        line=line,
        expense_name=name,
        keyword=keyword,
        carries_shop_money=carries_shop_money,
    )


def _reviewed(name, *, title="Prekė", amount=1, price=100, is_deposit=False, **review):
    line = _line(title=title, amount=amount, price=price, is_deposit=is_deposit)
    return _review(line, name, **review)


def _save(journal, account, lines, *, shop_money=0, on=IMPORT_DATE):
    return ReceiptImport.save(
        lines=tuple(lines),
        shop_money=shop_money,
        date=on,
        account=account,
        journal=journal,
    )


def test_shop_money_apply_zero_amount_leaves_lines_unchanged():
    lines = (_reviewed(ExpenseNameFactory(), price=679, carries_shop_money=True),)

    actual = ShopMoney.apply(lines, 0)

    assert actual == lines


@pytest.mark.parametrize(
    "specs, price, quantity",
    [
        pytest.param(
            [
                {"title": "VYTAUTAS 1.5 l", "amount": 3, "price": 255},
                {
                    "title": "PET (depozitinis)",
                    "amount": 3,
                    "price": 30,
                    "is_deposit": True,
                },
            ],
            285,
            3,
            id="deposit_line_excluded_from_quantity",
        ),
        pytest.param(
            [{"amount": 6}, {"amount": 1}, {"amount": 1}],
            300,
            8,
            id="amounts_summed_across_lines",
        ),
        pytest.param(
            [
                {"title": "pupelės", "amount": 1},
                {"title": "svogūnai", "amount": 1},
                {"title": "paprikos", "amount": 1},
            ],
            300,
            3,
            id="weighed_lines_each_count_as_one",
        ),
        pytest.param(
            [{"amount": 3, "price": 30, "is_deposit": True}],
            30,
            1,
            id="deposit_only_lines_quantity_is_one",
        ),
    ],
)
def test_expense_groups_sum_price_and_quantity(specs, price, quantity):
    name = ExpenseNameFactory(title="Mineralinis")
    lines = tuple(_reviewed(name, **spec) for spec in specs)

    groups = ExpenseGroups.build(lines)

    assert groups == [ExpenseGroup(expense_name=name, price=price, quantity=quantity)]


def test_expense_groups_one_group_per_expense_name():
    pieno = ExpenseNameFactory(title="Pieno produkai")
    darzoves = ExpenseNameFactory(title="Daržovės")
    lines = (
        _reviewed(pieno, amount=1),
        _reviewed(darzoves, amount=1),
        _reviewed(pieno, amount=1),
    )

    groups = ExpenseGroups.build(lines)

    assert [g.expense_name for g in groups] == [pieno, darzoves]


def test_receipt_import_fixture_lines_save_expenses_summing_7135(
    journal, account, expense_type
):
    receipt = ReceiptReader.read(FIXTURES / "barbora.pdf")
    expense_name = ExpenseNameFactory(title="Įvairios prekės", parent=expense_type)
    lines = [_review(line, expense_name) for line in receipt.lines]

    expenses = _save(journal, account, lines, on=date(2026, 9, 18))

    assert sum(expense.price for expense in expenses) == 7135


def _seven_lines(expense_names, *, flagged_index=4):
    prices = (100, 150, 200, 130, 679, 148, 150)
    return [
        _reviewed(
            expense_names[i],
            title=f"Prekė {i}",
            price=price,
            keyword=f"prekė{i}",
            carries_shop_money=(i == flagged_index),
        )
        for i, price in enumerate(prices)
    ]


@pytest.mark.parametrize(
    "skipped, saved_total",
    [
        pytest.param((), 1451, id="no_line_skipped"),
        # the flagged line stays flagged on itself: skipping the line before it
        # must not shift the discount
        pytest.param((3,), 1321, id="the_line_before_it_skipped"),
    ],
)
def test_receipt_import_shop_money_lowers_the_flagged_line_regardless_of_position(
    journal, account, expense_type, skipped, saved_total
):
    expense_names = [
        ExpenseNameFactory(title=f"Pavadinimas {i}", parent=expense_type)
        for i in range(7)
    ]
    lines = _seven_lines(expense_names)
    assert sum(reviewed.line.price for reviewed in lines) == 1557
    kept = [reviewed for i, reviewed in enumerate(lines) if i not in skipped]

    expenses = _save(journal, account, kept, shop_money=106)

    assert sum(expense.price for expense in expenses) == saved_total
    assert Expense.objects.get(expense_name=expense_names[4]).price == 573


@pytest.mark.parametrize(
    "old_keywords",
    [
        pytest.param(False, id="new_keywords"),
        pytest.param(True, id="existing_keywords"),
    ],
)
def test_receipt_import_keyword_query_count_does_not_grow_with_lines(
    journal, account, expense_type, first_name, old_keywords
):
    def save_count(count):
        lines = []
        for i in range(count):
            name = ExpenseNameFactory(
                title=f"Pavadinimas {count}-{i}", parent=expense_type
            )
            keyword = f"kw{count}-{i}"
            if old_keywords:
                ExpenseKeywordFactory(
                    journal=journal, keyword=keyword, expense_name=first_name
                )
            lines.append(_reviewed(name, keyword=keyword))
        return count_queries(lambda: _save(journal, account, lines))

    assert save_count(2) == save_count(6)


def test_receipt_import_repoints_an_existing_keyword_to_the_last_choice(
    journal, account, first_name, last_name
):
    existing = ExpenseKeywordFactory(
        journal=journal, keyword="jogurt", expense_name=first_name
    )

    _save(
        journal,
        account,
        [_reviewed(last_name, title="Jogurt kažkoks", keyword="Jogurt")],
    )

    existing.refresh_from_db()
    assert existing.expense_name == last_name
    assert list(ExpenseKeyword.objects.filter(journal=journal)) == [existing]


def test_receipt_import_two_lines_same_new_keyword_last_choice_wins(
    journal, account, first_name, last_name
):
    lines = [
        _reviewed(first_name, title="Jogurtas natūralus", keyword="jogurt"),
        _reviewed(last_name, title="Jogurtas graikiškas", price=150, keyword="jogurt"),
    ]

    _save(journal, account, lines)

    keywords = ExpenseKeyword.objects.filter(journal=journal, keyword="jogurt")
    assert keywords.count() == 1
    assert keywords.first().expense_name == last_name


def test_receipt_import_same_keyword_in_another_journal_is_untouched(
    journal, account, second_user, last_name
):
    # the factory gets or creates a type by title alone, so the other journal's
    # type has its own
    other_type = ExpenseTypeFactory(title="Kita", journal=second_user.journal)
    other_name = ExpenseNameFactory(title="Kita", parent=other_type)
    other_keyword = ExpenseKeywordFactory(
        journal=second_user.journal, keyword="pienas", expense_name=other_name
    )

    _save(journal, account, [_reviewed(last_name, title="Pienas", keyword="pienas")])

    other_keyword.refresh_from_db()
    assert other_keyword.expense_name == other_name

    created = ExpenseKeyword.objects.get(journal=journal, keyword="pienas")
    assert created.expense_name == last_name
    assert created.pk != other_keyword.pk


@pytest.mark.parametrize(
    "old_keywords, keywords_after",
    [
        pytest.param((), {}, id="new_keywords"),
        pytest.param(("pienas",), {"pienas": "Sena"}, id="repointed_keyword"),
    ],
)
def test_receipt_import_rolls_back_expenses_and_keywords_on_failure(
    journal, account, first_name, last_name, mocker, old_keywords, keywords_after
):
    for keyword in old_keywords:
        ExpenseKeywordFactory(journal=journal, keyword=keyword, expense_name=first_name)
    lines = [
        _reviewed(last_name, title="Pienas", keyword="pienas"),
        _reviewed(last_name, title="Sviestas", price=200, keyword="sviest"),
    ]
    mocker.patch(
        "project.expenses.services.receipt_import.ExpenseKeyword.objects.bulk_create",
        side_effect=RuntimeError,
    )

    with pytest.raises(RuntimeError):
        _save(journal, account, lines)

    assert Expense.objects.count() == 0
    assert (
        dict(ExpenseKeyword.objects.values_list("keyword", "expense_name__title"))
        == keywords_after
    )


def test_receipt_import_of_no_lines_saves_nothing_and_skips_the_sync(
    journal, account, mocker
):
    sync = mocker.patch("project.bookkeeping.balance_sources.sync_accounts")

    expenses = _save(journal, account, ())

    assert expenses == []
    assert Expense.objects.count() == 0
    assert sync.call_count == 0


def test_receipt_import_syncs_balance_once_and_updates_journal_first_record(
    main_user, journal, account, first_name, last_name, mocker
):
    sync = mocker.patch(
        "project.bookkeeping.balance_sources.sync_accounts",
        wraps=balance_sources.sync_accounts,
    )
    lines = [_reviewed(first_name, price=100), _reviewed(last_name, price=50)]
    import_date = date(1998, 6, 1)

    _save(journal, account, lines, on=import_date)

    assert Expense.objects.count() == 2
    assert sync.call_count == 1

    journal.refresh_from_db()
    assert journal.first_record == import_date

    balance = AccountBalanceModelService(main_user).year(1998).get(account=account)
    assert balance.expenses == 150
