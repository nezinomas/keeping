from datetime import date
from typing import NamedTuple

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....bookkeeping import balance_sources
from ....bookkeeping.tests.factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from ....debts.services.model_services import DebtModelService
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

# the edit puts the row before the journal's first record
EARLIER = {"date": date(1998, 1, 1)}


class Wiring(NamedTuple):
    factory: type
    edits: dict
    on_save: list
    on_delete: list


# the receivers a save or delete reaches, in call order
WIRING = {
    "Income": Wiring(
        IncomeFactory, EARLIER, ["accounts", "first_record"], ["accounts"]
    ),
    "Expense": Wiring(
        ExpenseFactory, EARLIER, ["accounts", "first_record"], ["accounts"]
    ),
    "Saving": Wiring(
        SavingFactory, {}, ["accounts", "savings"], ["accounts", "savings"]
    ),
    "Transaction": Wiring(TransactionFactory, {}, ["accounts"], ["accounts"]),
    "SavingClose": Wiring(
        SavingCloseFactory,
        {},
        ["accounts", "close_year", "savings"],
        ["accounts", "close_year", "savings"],
    ),
    "SavingChange": Wiring(
        SavingChangeFactory,
        {},
        ["close_year", "savings"],
        ["close_year", "savings"],
    ),
    "Debt": Wiring(BorrowFactory, {}, ["accounts"], ["accounts"]),
    "DebtReturn": Wiring(
        BorrowReturnFactory,
        {},
        ["accounts", "debt"],
        ["accounts", "debt"],
    ),
    "Pension": Wiring(PensionFactory, {}, ["pensions"], ["pensions"]),
    "SavingType": Wiring(SavingTypeFactory, {}, ["accounts", "savings"], []),
    "PensionType": Wiring(PensionTypeFactory, {}, ["pensions"], []),
    "AccountWorth": Wiring(AccountWorthFactory, {}, ["accounts"], []),
    "SavingWorth": Wiring(SavingWorthFactory, {}, ["savings"], []),
    "PensionWorth": Wiring(PensionWorthFactory, {}, ["pensions"], []),
}


@pytest.fixture
def listen(mocker):
    """Patch what each receiver calls onto one parent, whose `mock_calls` list in
    order what a save or delete reached; call it after the row is made."""

    def install():
        parent = mocker.Mock()
        mocker.patch.object(balance_sources, "sync_accounts", parent.accounts)
        mocker.patch.object(balance_sources, "sync_savings", parent.savings)
        mocker.patch.object(balance_sources, "sync_pensions", parent.pensions)
        mocker.patch.object(FundCloseYear, "follow", parent.close_year)
        mocker.patch.object(Journal, "save", parent.first_record)
        # the real body runs, so a sync it triggers itself shows in the order
        returned = mocker.patch.object(
            DebtModelService,
            "sync_returned",
            autospec=True,
            side_effect=DebtModelService.sync_returned,
        )
        parent.attach_mock(returned, "debt")

        return lambda: [call[0] for call in parent.mock_calls]

    return install


def created(name):
    """The row is made before the recorder listens, so only its own save counts."""
    wiring = WIRING[name]
    instance = wiring.factory()
    for field, value in wiring.edits.items():
        setattr(instance, field, value)

    return instance


@pytest.mark.django_db
@pytest.mark.parametrize("name", WIRING)
def test_save_reaches_receivers_in_order(name, listen):
    instance = created(name)
    reached = listen()

    instance.save()

    assert reached() == WIRING[name].on_save


@pytest.mark.django_db
@pytest.mark.parametrize("name", WIRING)
def test_delete_reaches_receivers_in_order(name, listen):
    instance = created(name)
    reached = listen()

    instance.delete()

    assert reached() == WIRING[name].on_delete


@pytest.mark.django_db
def test_deleting_a_debt_syncs_the_accounts_once_for_all_its_returns(listen):
    debt = BorrowFactory()
    BorrowReturnFactory.create_batch(2, debt=debt)
    reached = listen()

    debt.delete()

    assert reached() == ["accounts"]


@pytest.mark.django_db
def test_deleting_a_debt_costs_the_same_queries_for_2_and_6_returns():
    def queries_to_delete(returns):
        debt = BorrowFactory()
        BorrowReturnFactory.create_batch(returns, debt=debt)
        with CaptureQueriesContext(connection) as queries:
            debt.delete()
        return len(queries)

    assert queries_to_delete(2) == queries_to_delete(6)
