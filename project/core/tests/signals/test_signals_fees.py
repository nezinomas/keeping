from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....bookkeeping.tests.factories import SavingWorthFactory
from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingBalance, SavingType
from ....savings.services.model_services import SavingModelService
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ...services import signals_service

pytestmark = pytest.mark.django_db

WORTH_DATE = datetime(1999, 12, 31, 12, tzinfo=ZoneInfo("Europe/Vilnius"))


def _account_balance(account):
    return AccountBalance.objects.get(account=account, year=1999)


def _saving_balance(saving_type):
    return SavingBalance.objects.get(saving_type=saving_type, year=1999)


def _table(model):
    return sorted(
        tuple(sorted((k, v) for k, v in row.items() if k != "id"))
        for row in model.objects.values()
    )


# ----------------------------------------------------------------------------
#                                                   purchase -> account balance
# ----------------------------------------------------------------------------
def test_fee_only_purchase_leaves_the_account_untouched():
    account = AccountFactory(title="SEB")
    IncomeFactory(account=account, price=1000)

    SavingFactory(account=account, price=None, fee=100)

    actual = _account_balance(account)
    assert actual.expenses == 0
    assert actual.balance == 1000


def test_fee_only_purchase_counts_its_fee_in_the_saving():
    saving_type = SavingTypeFactory(title="Finbee")

    SavingFactory(saving_type=saving_type, price=None, fee=100)

    actual = _saving_balance(saving_type)
    assert actual.incomes == 0
    assert actual.fee == 100


def test_account_is_debited_prices_only_beside_fee_only_purchases():
    account = AccountFactory(title="SEB")

    SavingFactory(account=account, price=20000, fee=None)
    SavingFactory(account=account, price=None, fee=100)
    SavingFactory(account=account, price=0, fee=100)
    SavingFactory(account=account, price=10000, fee=100)

    assert _account_balance(account).expenses == 30000


def test_one_account_paying_two_saving_types_is_debited_both_prices():
    account = AccountFactory(title="IB")

    SavingFactory(
        account=account, saving_type=SavingTypeFactory(title="A"), price=200, fee=3
    )
    SavingFactory(
        account=account, saving_type=SavingTypeFactory(title="B"), price=600, fee=1
    )

    assert _account_balance(account).expenses == 800


# ----------------------------------------------------------------------------
#                                                       profit, end to end
# ----------------------------------------------------------------------------
def test_profit_subtracts_the_fee_once():
    saving_type = SavingTypeFactory(title="Fund")
    SavingFactory(saving_type=saving_type, price=200, fee=3)

    SavingWorthFactory(saving_type=saving_type, price=210, date=WORTH_DATE)

    actual = _saving_balance(saving_type)
    assert actual.incomes == 200
    assert actual.fee == 3
    assert actual.market_value == 210
    assert actual.profit_sum == 7
    assert actual.profit_proc == 3.5


def test_fee_entered_inside_the_price_is_subtracted_again_from_profit():
    ib = AccountFactory(title="Interactive Brokers")
    vall = SavingTypeFactory(title="VALL")
    IncomeFactory(account=ib, price=85000)

    SavingFactory(account=ib, saving_type=vall, price=20300, fee=300)
    SavingFactory(account=ib, saving_type=vall, price=60128, fee=128)
    SavingWorthFactory(saving_type=vall, price=80100, date=WORTH_DATE)

    account = _account_balance(ib)
    assert account.expenses == 80428
    assert account.balance == 4572

    saving = _saving_balance(vall)
    assert saving.incomes == 80428
    assert saving.fee == 428
    assert saving.profit_sum == -756
    assert saving.profit_proc == -0.94


def test_finbee_fee_only_rows_paid_from_two_accounts():
    seb = AccountFactory(title="SEB")
    revolut = AccountFactory(title="Revolut")
    finbee = SavingTypeFactory(title="Finbee")
    IncomeFactory(account=seb, price=5000)
    IncomeFactory(account=revolut, price=5000)

    SavingFactory(account=seb, saving_type=finbee, price=1000, fee=None)
    SavingFactory(account=seb, saving_type=finbee, price=None, fee=100)
    SavingFactory(account=revolut, saving_type=finbee, price=None, fee=100)
    SavingWorthFactory(saving_type=finbee, price=1200, date=WORTH_DATE)

    assert _account_balance(seb).balance == 4000
    assert _account_balance(revolut).balance == 5000

    saving = _saving_balance(finbee)
    assert saving.incomes == 1000
    assert saving.fee == 200
    assert saving.profit_sum == 0
    assert saving.profit_proc == 0.0


# ----------------------------------------------------------------------------
#                                                   switches, journals, types
# ----------------------------------------------------------------------------
def test_switch_with_a_fee_touches_no_account():
    SavingChangeFactory(price=100, fee=5)

    assert SavingBalance.objects.filter(year=1999).count() == 2
    assert AccountBalance.objects.count() == 0


def test_other_journal_purchase_does_not_reach_this_journal(main_user, second_user):
    mine = AccountFactory(title="Mine")
    SavingFactory(account=mine, price=200, fee=3)

    theirs = AccountFactory(title="Theirs", journal=second_user.journal)
    SavingFactory(
        account=theirs,
        saving_type=SavingTypeFactory(title="Theirs", journal=second_user.journal),
        price=900,
        fee=9,
    )

    assert _account_balance(mine).expenses == 200
    assert _account_balance(theirs).expenses == 900


def test_saving_a_saving_type_leaves_every_balance_unchanged():
    account = AccountFactory(title="IB")
    saving_type = SavingTypeFactory(title="VALL")
    SavingFactory(account=account, saving_type=saving_type, price=200, fee=3)
    SavingWorthFactory(saving_type=saving_type, price=210, date=WORTH_DATE)
    accounts, savings = _table(AccountBalance), _table(SavingBalance)

    saving_type.title = "VALL renamed"
    saving_type.save()

    assert _table(AccountBalance) == accounts
    assert _table(SavingBalance) == savings


# ----------------------------------------------------------------------------
#                                         a fresh re-sync agrees with signals
# ----------------------------------------------------------------------------
def test_resync_reproduces_the_rows_the_signals_wrote(main_user):
    seb = AccountFactory(title="SEB")
    ib = AccountFactory(title="IB")
    fund = SavingTypeFactory(title="Fund")
    finbee = SavingTypeFactory(title="Finbee")
    IncomeFactory(account=seb, price=5000, date=date(1998, 1, 1))
    IncomeFactory(account=ib, price=5000)
    SavingFactory(account=seb, saving_type=finbee, price=1000, date=date(1998, 1, 1))
    SavingFactory(account=seb, saving_type=finbee, price=None, fee=100)
    SavingFactory(account=ib, saving_type=fund, price=200, fee=3)
    SavingWorthFactory(saving_type=fund, price=310, date=WORTH_DATE)
    # last, so a signal it fails to send is not covered by a later one
    SavingChangeFactory(from_account=finbee, to_account=fund, price=100, fee=5)
    accounts, savings = _table(AccountBalance), _table(SavingBalance)

    signals_service.sync_accounts(instance=None, user=main_user)
    signals_service.sync_savings(instance=None, user=main_user)

    assert _table(AccountBalance) == accounts
    assert _table(SavingBalance) == savings


# ----------------------------------------------------------------------------
#                                                                 query counts
# ----------------------------------------------------------------------------
def _expenses_queries(user, count):
    for i in range(count):
        SavingFactory(
            account=AccountFactory(title=f"A{i}"),
            saving_type=SavingTypeFactory(title=f"S{i}"),
            fee=i,
        )

    with CaptureQueriesContext(connection) as queries:
        list(SavingModelService(user).expenses())

    return len(queries)


def test_purchase_expenses_query_count_does_not_grow(main_user):
    two = _expenses_queries(main_user, 2)
    SavingType.objects.all().delete()

    assert _expenses_queries(main_user, 6) == two
