from datetime import date
from typing import NamedTuple

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....accounts.models import Account, AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....bookkeeping import balance_sources
from ....bookkeeping.tests.factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from ....bookkeeping.tests.helper import quiet_build
from ....debts.models import Debt
from ....debts.services.model_services import DebtModelService
from ....debts.tests.factories import BorrowFactory, BorrowReturnFactory
from ....expenses.tests.factories import ExpenseFactory
from ....incomes.models import Income
from ....incomes.tests.factories import IncomeFactory
from ....journals.models import Journal
from ....pensions.models import Pension, PensionBalance, PensionType
from ....pensions.tests.factories import PensionFactory, PensionTypeFactory
from ....savings.models import Saving, SavingBalance, SavingType
from ....savings.tests.factories import (
    SavingFactory,
    SavingTypeFactory,
)
from ....transactions.close_rules import CLOSE
from ....transactions.models import SavingChange, SavingClose
from ....transactions.services.close_year import FundCloseYear
from ....transactions.tests.factories import (
    SavingChangeFactory,
    SavingCloseFactory,
    TransactionFactory,
)

pytestmark = pytest.mark.django_db

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
    "Account": Wiring(AccountFactory, {}, ["accounts"], []),
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


@pytest.mark.parametrize("name", WIRING)
def test_save_reaches_receivers_in_order(name, listen):
    instance = created(name)
    reached = listen()

    instance.save()

    assert reached() == WIRING[name].on_save


@pytest.mark.parametrize("name", WIRING)
def test_delete_reaches_receivers_in_order(name, listen):
    instance = created(name)
    reached = listen()

    instance.delete()

    assert reached() == WIRING[name].on_delete


@pytest.mark.parametrize("name", ["Account", "SavingType", "PensionType"])
def test_creating_a_type_reaches_its_receivers_once(name, listen, main_user):
    journal = main_user.journal
    reached = listen()

    WIRING[name].factory(journal=journal)

    assert reached() == WIRING[name].on_save


def test_deleting_a_debt_syncs_the_accounts_once_for_all_its_returns(listen):
    debt = BorrowFactory()
    BorrowReturnFactory.create_batch(2, debt=debt)
    reached = listen()

    debt.delete()

    assert reached() == ["accounts"]


def test_deleting_a_debt_costs_the_same_queries_for_2_and_6_returns():
    def queries_to_delete(returns):
        debt = BorrowFactory()
        BorrowReturnFactory.create_batch(returns, debt=debt)
        with CaptureQueriesContext(connection) as queries:
            debt.delete()
        return len(queries)

    assert queries_to_delete(2) == queries_to_delete(6)


def _journal_state():
    """Every balance row, and what the receivers write besides; an owner shows as its
    title, not its pk."""
    snapshot = {}
    for model in (AccountBalance, SavingBalance, PensionBalance):
        fields = [
            f"{f.name}__title" if f.is_relation else f.name
            for f in model._meta.concrete_fields
            if not f.primary_key
        ]
        rows = model.objects.values_list(*fields)
        snapshot[model.__name__] = sorted(rows, key=repr)
    snapshot["first_record"] = list(Journal.objects.values_list("first_record"))
    snapshot["closed"] = sorted(SavingType.objects.values_list("title", "closed"))
    snapshot["returned"] = list(Debt.objects.values_list("name", "returned"))
    return snapshot


def _build_a_journal():
    bank = AccountFactory(title="Bank")
    fund = SavingTypeFactory(title="Fund")
    other = SavingTypeFactory(title="Other")
    old = SavingTypeFactory(title="Old", closed=2000)
    pension_type = PensionTypeFactory(title="Pension")
    SavingFactory(saving_type=fund, account=bank, date=date(1999, 1, 1))
    SavingCloseFactory(
        from_account=fund, to_account=bank, price=7, date=date(1999, 6, 1)
    )
    SavingChangeFactory(
        from_account=fund, to_account=other, price=3, date=date(1999, 7, 1)
    )
    SavingWorthFactory(saving_type=fund, price=90)
    SavingFactory(saving_type=old, account=bank, date=date(1999, 2, 1))
    sold = SavingTypeFactory(title="Sold")
    SavingFactory(saving_type=sold, account=bank, date=date(1999, 1, 1))
    closing = SavingCloseFactory.build(
        from_account=sold, to_account=bank, price=5, date=date(2001, 3, 1)
    )
    closing.close_rule = CLOSE
    closing.save()
    PensionFactory(pension_type=pension_type)
    PensionWorthFactory(pension_type=pension_type, price=120)
    IncomeFactory(account=bank, **EARLIER)
    debt = BorrowFactory(name="Lender", account=bank)
    BorrowReturnFactory(debt=debt, account=bank)


def test_a_quiet_build_leaves_what_a_per_save_build_leaves(main_user):
    first_record = main_user.journal.first_record
    _build_a_journal()
    per_save = _journal_state()
    assert all(per_save.values())
    records = (SavingClose, SavingChange, Saving, Pension, Income, Debt)
    for model in (*records, Account, SavingType, PensionType):
        model.objects.all().delete()
    for model in (AccountBalance, SavingBalance, PensionBalance):
        model.objects.all().delete()
    Journal.objects.update(first_record=first_record)

    with quiet_build(main_user):
        _build_a_journal()

    assert _journal_state() == per_save
