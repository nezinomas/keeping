from datetime import date

import pytest

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....bookkeeping.tests.factories import SavingWorthFactory
from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingBalance, SavingType
from ....savings.services.model_services import SavingModelService
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from ...lib.db_sync import SAVING_FIELDS
from ...services import signals_service
from ...tests.utils import count_queries
from .helpers import balance, worth_date

pytestmark = pytest.mark.django_db


def _account_balance(account):
    return AccountBalance.objects.get(account=account, year=1999)


def _table(model):
    return sorted(
        tuple(sorted((k, v) for k, v in row.items() if k != "id"))
        for row in model.objects.values()
    )


# purchase -> account balance
def test_fee_only_purchase_leaves_the_account_untouched():
    account = AccountFactory(title="SEB")
    IncomeFactory(account=account, price=1000)

    SavingFactory(account=account, price=0, fee=100)

    actual = _account_balance(account)
    assert actual.expenses == 0
    assert actual.balance == 1000


def test_fee_only_purchase_counts_its_fee_in_the_saving():
    saving_type = SavingTypeFactory(title="Finbee")

    SavingFactory(saving_type=saving_type, price=0, fee=100)

    actual = balance(saving_type)
    assert actual.incomes == 0
    assert actual.fee == 100


def test_account_is_debited_prices_only_beside_fee_only_purchases():
    account = AccountFactory(title="SEB")

    SavingFactory(account=account, price=20000, fee=0)
    SavingFactory(account=account, price=0, fee=100)
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


# profit, end to end
def test_profit_subtracts_the_fee_once():
    saving_type = SavingTypeFactory(title="Fund")
    SavingFactory(saving_type=saving_type, price=200, fee=3)

    SavingWorthFactory(saving_type=saving_type, price=210, date=worth_date())

    actual = balance(saving_type)
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
    SavingWorthFactory(saving_type=vall, price=80100, date=worth_date())

    account = _account_balance(ib)
    assert account.expenses == 80428
    assert account.balance == 4572

    saving = balance(vall)
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

    SavingFactory(account=seb, saving_type=finbee, price=1000, fee=0)
    SavingFactory(account=seb, saving_type=finbee, price=0, fee=100)
    SavingFactory(account=revolut, saving_type=finbee, price=0, fee=100)
    SavingWorthFactory(saving_type=finbee, price=1200, date=worth_date())

    assert _account_balance(seb).balance == 4000
    assert _account_balance(revolut).balance == 5000

    saving = balance(finbee)
    assert saving.incomes == 1000
    assert saving.fee == 200
    assert saving.profit_sum == 0
    assert saving.profit_proc == 0.0


# switches, journals, types
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
    SavingWorthFactory(saving_type=saving_type, price=210, date=worth_date())
    accounts, savings = _table(AccountBalance), _table(SavingBalance)

    saving_type.title = "VALL renamed"
    saving_type.save()

    assert _table(AccountBalance) == accounts
    assert _table(SavingBalance) == savings


# fee charged to the account
def test_account_charged_fee_is_debited_with_the_price():
    account = AccountFactory(title="IB")
    vall = SavingTypeFactory(title="VALL", fee_source=SavingType.FeeSource.ACCOUNT)

    SavingFactory(account=account, saving_type=vall, price=200, fee=3)

    assert _account_balance(account).expenses == 203


def test_account_charged_fee_only_purchase_debits_its_fee():
    account = AccountFactory(title="IB")
    vall = SavingTypeFactory(title="VALL", fee_source=SavingType.FeeSource.ACCOUNT)

    SavingFactory(account=account, saving_type=vall, price=0, fee=100)

    assert _account_balance(account).expenses == 100


def test_one_account_paying_both_fee_sources():
    account = AccountFactory(title="IB")
    vall = SavingTypeFactory(title="VALL", fee_source=SavingType.FeeSource.ACCOUNT)
    fund = SavingTypeFactory(title="Fund")

    SavingFactory(account=account, saving_type=vall, price=200, fee=3)
    SavingFactory(account=account, saving_type=fund, price=600, fee=1)
    SavingFactory(account=account, saving_type=vall, price=0, fee=2)

    assert _account_balance(account).expenses == 805


def test_fee_source_does_not_change_the_saving_balance():
    balances = {}
    for title, fee_source in (
        ("A", SavingType.FeeSource.INVESTMENT),
        ("B", SavingType.FeeSource.ACCOUNT),
    ):
        saving_type = SavingTypeFactory(title=title, fee_source=fee_source)
        SavingFactory(saving_type=saving_type, price=200, fee=3)
        SavingFactory(saving_type=saving_type, price=0, fee=1)
        SavingWorthFactory(saving_type=saving_type, price=210, date=worth_date())
        balances[title] = (
            SavingBalance.objects.filter(saving_type=saving_type)
            .order_by("year")
            .values(*[f for f in SAVING_FIELDS if f != "latest_check"])
        )

    assert len(balances["A"]) == 2
    assert list(balances["A"]) == list(balances["B"])


def test_switching_a_types_fee_source_re_syncs_its_account():
    account = AccountFactory(title="IB")
    vall = SavingTypeFactory(title="VALL")
    SavingFactory(account=account, saving_type=vall, price=200, fee=3)
    assert _account_balance(account).expenses == 200

    vall.fee_source = SavingType.FeeSource.ACCOUNT
    vall.save()

    actual = _account_balance(account)
    assert actual.expenses == 203
    assert actual.balance == -203
    assert actual.delta == 203


def test_switching_a_type_re_syncs_only_its_own_journal(main_user, second_user, mocker):
    theirs = AccountFactory(title="Theirs", journal=second_user.journal)
    their_type = SavingTypeFactory(
        title="Their VALL",
        journal=second_user.journal,
        fee_source=SavingType.FeeSource.ACCOUNT,
    )
    SavingFactory(account=theirs, saving_type=their_type, price=900, fee=9)
    mine = SavingTypeFactory(title="My VALL")
    SavingFactory(account=AccountFactory(title="Mine"), saving_type=mine)
    assert _account_balance(theirs).expenses == 909
    # a re-sync of their journal would put 909 back
    AccountBalance.objects.filter(account=theirs).update(expenses=1)
    sync = mocker.spy(signals_service, "sync_accounts")

    mine.fee_source = SavingType.FeeSource.ACCOUNT
    mine.save()

    assert [call.args[0] for call in sync.call_args_list] == [main_user]
    assert _account_balance(theirs).expenses == 1


# a fresh re-sync agrees with signals
def test_resync_reproduces_the_rows_the_signals_wrote(main_user):
    seb = AccountFactory(title="SEB")
    ib = AccountFactory(title="IB")
    fund = SavingTypeFactory(title="Fund")
    finbee = SavingTypeFactory(title="Finbee")
    IncomeFactory(account=seb, price=5000, date=date(1998, 1, 1))
    IncomeFactory(account=ib, price=5000)
    SavingFactory(account=seb, saving_type=finbee, price=1000, date=date(1998, 1, 1))
    SavingFactory(account=seb, saving_type=finbee, price=0, fee=100)
    SavingFactory(account=ib, saving_type=fund, price=200, fee=3)
    SavingWorthFactory(saving_type=fund, price=310, date=worth_date())
    # last, so a signal it fails to send is not covered by a later one
    SavingChangeFactory(from_account=finbee, to_account=fund, price=100, fee=5)
    accounts, savings = _table(AccountBalance), _table(SavingBalance)

    signals_service.sync_accounts(user=main_user)
    signals_service.sync_savings(user=main_user)

    assert _table(AccountBalance) == accounts
    assert _table(SavingBalance) == savings


# query counts
def _purchases_of_both_fee_sources(count):
    for i in range(count):
        fee_source = (
            SavingType.FeeSource.ACCOUNT if i % 2 else SavingType.FeeSource.INVESTMENT
        )
        SavingFactory(
            account=AccountFactory(title=f"A{i}"),
            saving_type=SavingTypeFactory(title=f"S{i}", fee_source=fee_source),
            fee=i,
        )


@pytest.mark.parametrize(
    "run",
    [
        lambda user: list(SavingModelService(user).expenses()),
        lambda user: signals_service.sync_accounts(user=user),
    ],
    ids=["expenses", "re-sync"],
)
def test_query_count_does_not_grow_with_both_fee_sources(main_user, run):
    _purchases_of_both_fee_sources(2)
    two = count_queries(lambda: run(main_user))
    SavingType.objects.all().delete()

    _purchases_of_both_fee_sources(6)

    assert count_queries(lambda: run(main_user)) == two
