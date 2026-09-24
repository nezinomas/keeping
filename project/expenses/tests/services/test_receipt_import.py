from datetime import date

import pytest

from ....accounts.services.model_services import AccountBalanceModelService
from ....accounts.tests.factories import AccountFactory
from ....core.services import signals_service as signals_service_module
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


def _line(title="Prekė", amount=1, price=100, is_deposit=False):
    return ReceiptLine(title=title, amount=amount, price=price, is_deposit=is_deposit)


def test_shop_money_apply_zero_amount_leaves_lines_unchanged():
    name = ExpenseNameFactory()
    lines = (
        ReviewedLine(
            line=_line(price=679),
            expense_name=name,
            keyword="prekė",
            carries_shop_money=True,
        ),
    )

    actual = ShopMoney.apply(lines, 0)

    assert actual == lines


def test_shop_money_apply_subtracts_amount_from_flagged_line_only():
    name = ExpenseNameFactory()
    flagged = ReviewedLine(
        line=_line(title="Flagged", price=679),
        expense_name=name,
        keyword="flagged",
        carries_shop_money=True,
    )
    other = ReviewedLine(
        line=_line(title="Other", price=200),
        expense_name=name,
        keyword="other",
        carries_shop_money=False,
    )

    actual = ShopMoney.apply((flagged, other), 106)

    assert actual[0].line.price == 573
    assert actual[1].line.price == 200


def _reviewed(name, *, title="Prekė", amount=1, price=100, is_deposit=False):
    return ReviewedLine(
        line=_line(title=title, amount=amount, price=price, is_deposit=is_deposit),
        expense_name=name,
        keyword="prekė",
        carries_shop_money=False,
    )


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


def test_receipt_import_fixture_lines_save_expenses_summing_7135(main_user):
    receipt = ReceiptReader.read(FIXTURES / "barbora.pdf")
    expense_type = ExpenseTypeFactory(title="Maistas RI29", journal=main_user.journal)
    expense_name = ExpenseNameFactory(title="Įvairios prekės", parent=expense_type)
    account = AccountFactory(journal=main_user.journal)

    lines = tuple(
        ReviewedLine(
            line=line,
            expense_name=expense_name,
            keyword="prekė",
            carries_shop_money=False,
        )
        for line in receipt.lines
    )

    expenses = ReceiptImport.save(
        lines=lines,
        shop_money=0,
        date=date(2026, 9, 18),
        account=account,
        journal=main_user.journal,
    )

    assert sum(expense.price for expense in expenses) == 7135


def _seven_lines(expense_names, *, flagged_index=4):
    prices = (100, 150, 200, 130, 679, 148, 150)
    return [
        ReviewedLine(
            line=_line(title=f"Prekė {i}", price=price),
            expense_name=expense_names[i],
            keyword=f"prekė{i}",
            carries_shop_money=(i == flagged_index),
        )
        for i, price in enumerate(prices)
    ]


def _seven_expense_names(journal):
    expense_type = ExpenseTypeFactory(title="Maistas RI7", journal=journal)
    return [
        ExpenseNameFactory(title=f"Pavadinimas {i}", parent=expense_type)
        for i in range(7)
    ]


def test_receipt_import_shop_money_lowers_the_flagged_line_regardless_of_position(
    main_user,
):
    journal = main_user.journal
    account = AccountFactory(journal=journal)
    expense_names = _seven_expense_names(journal)
    lines = _seven_lines(expense_names)

    assert sum(reviewed.line.price for reviewed in lines) == 1557

    expenses = ReceiptImport.save(
        lines=tuple(lines),
        shop_money=106,
        date=date(2026, 1, 1),
        account=account,
        journal=journal,
    )

    assert sum(expense.price for expense in expenses) == 1451
    flagged = Expense.objects.get(expense_name=expense_names[4])
    assert flagged.price == 573

    # the flagged line stays flagged on itself, skipping the line before it
    # must not shift the discount
    Expense.objects.all().delete()
    lines_with_skip = [reviewed for i, reviewed in enumerate(lines) if i != 3]

    ReceiptImport.save(
        lines=tuple(lines_with_skip),
        shop_money=106,
        date=date(2026, 1, 1),
        account=account,
        journal=journal,
    )

    flagged = Expense.objects.get(expense_name=expense_names[4])
    assert flagged.price == 573


def test_receipt_import_repoints_existing_keyword_last_choice_wins(main_user):
    journal = main_user.journal
    expense_type = ExpenseTypeFactory(title="Maistas RIK", journal=journal)
    name_a = ExpenseNameFactory(title="Pieno produkai RIK", parent=expense_type)
    name_kita = ExpenseNameFactory(title="Kita RIK", parent=expense_type)
    ExpenseKeywordFactory(journal=journal, keyword="jogurt", expense_name=name_a)
    account = AccountFactory(journal=journal)

    lines = (
        ReviewedLine(
            line=_line(title="Jogurt kažkoks", price=100),
            expense_name=name_kita,
            keyword="Jogurt",
            carries_shop_money=False,
        ),
    )

    ReceiptImport.save(
        lines=lines,
        shop_money=0,
        date=date(2026, 1, 1),
        account=account,
        journal=journal,
    )

    keywords = ExpenseKeyword.objects.filter(journal=journal, keyword="jogurt")

    assert keywords.count() == 1
    assert keywords.first().expense_name == name_kita


def test_receipt_import_rolls_back_expenses_and_keywords_on_failure(main_user, mocker):
    journal = main_user.journal
    expense_type = ExpenseTypeFactory(title="Maistas RIF", journal=journal)
    name = ExpenseNameFactory(title="Pieno RIF", parent=expense_type)
    account = AccountFactory(journal=journal)
    lines = (
        ReviewedLine(
            line=_line(title="Pienas", price=100),
            expense_name=name,
            keyword="pienas",
            carries_shop_money=False,
        ),
        ReviewedLine(
            line=_line(title="Sviestas", price=200),
            expense_name=name,
            keyword="sviest",
            carries_shop_money=False,
        ),
    )
    update_or_create = ExpenseKeyword.objects.update_or_create

    def write_first_then_fail(**kwargs):
        if kwargs["keyword"] == "sviest":
            raise RuntimeError
        return update_or_create(**kwargs)

    mocker.patch(
        "project.expenses.services.receipt_import.ExpenseKeyword.objects"
        ".update_or_create",
        side_effect=write_first_then_fail,
    )

    with pytest.raises(RuntimeError):
        ReceiptImport.save(
            lines=lines,
            shop_money=0,
            date=date(2026, 1, 1),
            account=account,
            journal=journal,
        )

    assert Expense.objects.count() == 0
    assert ExpenseKeyword.objects.count() == 0


def test_receipt_import_of_no_lines_saves_nothing_and_skips_the_sync(main_user, mocker):
    sync = mocker.patch("project.core.signals.signals_service.sync_accounts")

    expenses = ReceiptImport.save(
        lines=(),
        shop_money=0,
        date=date(2026, 1, 1),
        account=AccountFactory(journal=main_user.journal),
        journal=main_user.journal,
    )

    assert expenses == []
    assert Expense.objects.count() == 0
    assert sync.call_count == 0


def test_receipt_import_syncs_balance_once_and_updates_journal_first_record(
    main_user, mocker
):
    journal = main_user.journal
    expense_type = ExpenseTypeFactory(title="Maistas RIB", journal=journal)
    name = ExpenseNameFactory(title="Pieno RIB", parent=expense_type)
    account = AccountFactory(journal=journal)

    sync = mocker.patch(
        "project.core.signals.signals_service.sync_accounts",
        wraps=signals_service_module.sync_accounts,
    )

    lines = (
        _reviewed(name, price=100),
        _reviewed(name, price=50),
    )
    import_date = date(1998, 6, 1)

    ReceiptImport.save(
        lines=lines,
        shop_money=0,
        date=import_date,
        account=account,
        journal=journal,
    )

    assert sync.call_count == 1

    journal.refresh_from_db()
    assert journal.first_record == import_date

    balance = AccountBalanceModelService(main_user).year(1998).get(account=account)
    assert balance.expenses == 150
