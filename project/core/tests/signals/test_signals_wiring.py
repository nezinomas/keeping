from datetime import date

import pytest

from ....bookkeeping.tests.factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from ....debts.services.model_services import DebtReturnModelService
from ....debts.tests.factories import BorrowFactory, BorrowReturnFactory
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.tests.factories import IncomeFactory
from ....journals.models import Journal
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.tests.factories import (
    SavingFactory,
    SavingTypeFactory,
)
from ....transactions.services.close_year import FundCloseYear
from ....transactions.tests.factories import (
    SavingChangeFactory,
    SavingCloseFactory,
    TransactionFactory,
)
from ...services import signals_service

# Calls a save or delete reaches, in order; update_debt_model saves its Debt,
# which syncs the accounts once more.
DEBT_RETURN = ["accounts", "debt", "accounts"]
WIRING = {
    "Income": (IncomeFactory, ["accounts", "first_record"], ["accounts"]),
    "Expense": (ExpenseFactory, ["accounts", "first_record"], ["accounts"]),
    "Saving": (SavingFactory, ["accounts", "savings"], ["accounts", "savings"]),
    "Transaction": (TransactionFactory, ["accounts"], ["accounts"]),
    "SavingClose": (
        SavingCloseFactory,
        ["accounts", "close_year", "savings"],
        ["accounts", "close_year", "savings"],
    ),
    "SavingChange": (
        SavingChangeFactory,
        ["close_year", "savings"],
        ["close_year", "savings"],
    ),
    "Debt": (BorrowFactory, ["accounts"], ["accounts"]),
    "DebtReturn": (BorrowReturnFactory, DEBT_RETURN, DEBT_RETURN),
    "Pension": (PensionFactory, ["pensions"], ["pensions"]),
    "SavingType": (SavingTypeFactory, ["accounts", "savings"], []),
    "PensionType": (PensionTypeFactory, ["pensions"], []),
    "AccountWorth": (AccountWorthFactory, ["accounts"], []),
    "SavingWorth": (SavingWorthFactory, ["savings"], []),
    "PensionWorth": (PensionWorthFactory, ["pensions"], []),
}


@pytest.fixture
def listen(mocker):
    """Patch what each receiver calls onto one parent, whose `mock_calls` list in
    order what a save or delete reached; call it after the row is made."""

    def install():
        parent = mocker.Mock()
        mocker.patch.object(signals_service, "sync_accounts", parent.accounts)
        mocker.patch.object(signals_service, "sync_savings", parent.savings)
        mocker.patch.object(signals_service, "sync_pensions", parent.pensions)
        mocker.patch.object(FundCloseYear, "follow", parent.close_year)
        mocker.patch.object(Journal, "save", parent.first_record)
        parent.debt.return_value = 0
        mocker.patch.object(
            DebtReturnModelService, "total_returned_for_debt", parent.debt
        )

        return lambda: [call[0] for call in parent.mock_calls]

    return install


def created(name):
    """The row is made before the recorder listens, so only its own save counts."""
    instance = WIRING[name][0]()
    if name in ("Income", "Expense"):
        instance.date = date(1998, 1, 1)  # before the journal's first record

    return instance


@pytest.mark.django_db
@pytest.mark.parametrize("name", WIRING)
def test_save_reaches_receivers_in_order(name, listen):
    instance = created(name)
    reached = listen()

    instance.save()

    assert reached() == WIRING[name][1]


@pytest.mark.django_db
@pytest.mark.parametrize("name", WIRING)
def test_delete_reaches_receivers_in_order(name, listen):
    instance = created(name)
    reached = listen()

    instance.delete()

    assert reached() == WIRING[name][2]


@pytest.mark.django_db
def test_income_save_syncs_accounts(main_user, mocker):
    accounts = mocker.spy(signals_service, "sync_accounts")

    IncomeFactory()

    assert mocker.call(main_user) in accounts.call_args_list


@pytest.mark.django_db
def test_saving_save_syncs_savings(main_user, mocker):
    savings = mocker.spy(signals_service, "sync_savings")

    SavingFactory()

    assert mocker.call(main_user) in savings.call_args_list


@pytest.mark.django_db
def test_pension_save_syncs_pensions(main_user, mocker):
    pensions = mocker.spy(signals_service, "sync_pensions")

    PensionFactory()

    assert mocker.call(main_user) in pensions.call_args_list
