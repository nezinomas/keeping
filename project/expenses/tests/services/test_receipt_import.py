from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....accounts.services.model_services import AccountBalanceModelService
from ....accounts.tests.factories import AccountFactory
from ....bookkeeping import balance_sources
from ...models import Expense, ExpenseKeyword
from ...receipts.reader import ReceiptReader
from ...receipts.receipt import ReceiptLine
from ...services.receipt_import import (
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


def test_shop_money_apply_subtracts_amount_from_flagged_line_only():
    name = ExpenseNameFactory()
    flagged = _reviewed(name, price=679, carries_shop_money=True)
    other = _reviewed(name, price=200)

    actual = ShopMoney.apply((flagged, other), 106)

    assert actual[0].line.price == 573
    assert actual[1].line.price == 200


def test_expense_groups_sums_price_and_quantity_deposit_line_excluded_from_quantity():
    mineralinis = ExpenseNameFactory(title="Mineralinis")
    lines = (
        _reviewed(mineralinis, title="VYTAUTAS 1.5 l", amount=3, price=255),
        _reviewed(
            mineralinis,
            title="PET (depozitinis)",
            amount=3,
            price=30,
            is_deposit=True,
        ),
    )

    groups = ExpenseGroups.build(lines)

    assert len(groups) == 1
    assert groups[0].expense_name == mineralinis
    assert groups[0].price == 285
    assert groups[0].quantity == 3


def test_expense_groups_quantity_sums_amounts_across_lines():
    pieno = ExpenseNameFactory(title="Pieno produkai")
    lines = (
        _reviewed(pieno, amount=6),
        _reviewed(pieno, amount=1),
        _reviewed(pieno, amount=1),
    )

    groups = ExpenseGroups.build(lines)

    assert groups[0].quantity == 8


def test_expense_groups_weighed_lines_each_count_as_one():
    darzoves = ExpenseNameFactory(title="Daržovės")
    lines = (
        _reviewed(darzoves, title="pupelės", amount=1),
        _reviewed(darzoves, title="svogūnai", amount=1),
        _reviewed(darzoves, title="paprikos", amount=1),
    )

    groups = ExpenseGroups.build(lines)

    assert groups[0].quantity == 3


def test_expense_groups_deposit_only_lines_quantity_is_one():
    mineralinis = ExpenseNameFactory(title="Mineralinis")
    lines = (_reviewed(mineralinis, amount=3, price=30, is_deposit=True),)

    groups = ExpenseGroups.build(lines)

    assert groups[0].quantity == 1


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
    journal, account, first_name, last_name, old_keywords
):
    def save_count(count):
        keywords = [f"kw{count}-{i}" for i in range(count)]
        if old_keywords:
            for keyword in keywords:
                ExpenseKeywordFactory(
                    journal=journal, keyword=keyword, expense_name=first_name
                )
        lines = [_reviewed(last_name, keyword=keyword) for keyword in keywords]
        with CaptureQueriesContext(connection) as ctx:
            _save(journal, account, lines)
        return len(ctx.captured_queries)

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


def test_receipt_import_of_no_lines_runs_no_keyword_query(journal, account):
    with CaptureQueriesContext(connection) as ctx:
        _save(journal, account, ())

    assert not any(
        "expenses_expensekeyword" in query["sql"].lower()
        for query in ctx.captured_queries
    )


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
