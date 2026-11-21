from datetime import date

import pytest

from ....accounts.models import AccountBalance
from ....accounts.tests.factories import AccountFactory
from ....bookkeeping import balance_sources
from ....bookkeeping.tests.helper import quiet_build
from ....core.lib.db_sync import SAVING_FIELDS
from ....core.tests.utils import count_queries
from ....incomes.tests.factories import IncomeFactory
from ....savings.models import SavingBalance, SavingType
from ....savings.services.model_services import SavingModelService
from ....savings.tests.factories import SavingFactory, SavingTypeFactory
from ....transactions.tests.factories import SavingChangeFactory
from .helpers import balance, worth

pytestmark = pytest.mark.django_db


def _account_balance(account):
    return AccountBalance.objects.get(account=account, year=1999)


def _table(model):
    return sorted(
        tuple(sorted((k, v) for k, v in row.items() if k != "id"))
        for row in model.objects.values()
    )


def test_fee_only_purchase_counts_its_fee_in_the_saving():
    saving_type = SavingTypeFactory(title="Finbee")

    SavingFactory(saving_type=saving_type, price=0, fee=100)

    actual = balance(saving_type)
    assert actual.incomes == 0
    assert actual.fee == 100


# the account holds 10,00 of incomes; (its expenses, its balance) once the last saves
@pytest.mark.parametrize(
    "fee_sources, seeded, last, expected",
    [
        pytest.param(
            {"VALL": SavingType.FeeSource.ACCOUNT},
            [],
            ("VALL", 200, 3),
            (203, 797),
            id="is-debited-with-the-price",
        ),
        pytest.param(
            {"VALL": SavingType.FeeSource.ACCOUNT},
            [],
            ("VALL", 0, 100),
            (100, 900),
            id="only-purchase-debits-its-fee",
        ),
        pytest.param(
            {"VALL": SavingType.FeeSource.INVESTMENT},
            [],
            ("VALL", 0, 100),
            (0, 1000),
            id="fee-only-purchase-charged-to-the-investment",
        ),
        pytest.param(
            {"VALL": SavingType.FeeSource.INVESTMENT},
            [("VALL", 20000, 0), ("VALL", 0, 100), ("VALL", 0, 100)],
            ("VALL", 10000, 100),
            (30000, -29000),
            id="prices-only-beside-fee-only-purchases",
        ),
        pytest.param(
            {
                "A": SavingType.FeeSource.INVESTMENT,
                "B": SavingType.FeeSource.INVESTMENT,
            },
            [("A", 200, 3)],
            ("B", 600, 1),
            (800, 200),
            id="two-types-charging-the-investment",
        ),
        pytest.param(
            {
                "VALL": SavingType.FeeSource.ACCOUNT,
                "Fund": SavingType.FeeSource.INVESTMENT,
            },
            [("VALL", 200, 3), ("Fund", 600, 1)],
            ("VALL", 0, 2),
            (805, 195),
            id="one-type-charging-the-account",
        ),
    ],
)
def test_one_account_is_debited_each_price_and_the_fees_its_types_charge_it(
    main_user, fee_sources, seeded, last, expected
):
    with quiet_build(main_user):
        account = AccountFactory(title="IB")
        IncomeFactory(account=account, price=1000)
        saving_types = {
            title: SavingTypeFactory(title=title, fee_source=fee_source)
            for title, fee_source in fee_sources.items()
        }
        for title, price, fee in seeded:
            SavingFactory(
                account=account, saving_type=saving_types[title], price=price, fee=fee
            )

    title, price, fee = last
    SavingFactory(
        account=account, saving_type=saving_types[title], price=price, fee=fee
    )

    actual = _account_balance(account)
    assert (actual.expenses, actual.balance) == expected


@pytest.mark.parametrize(
    "incomes, purchases, worth_price, expected_account, expected_saving",
    [
        pytest.param(
            [],
            [(200, 3)],
            210,
            (200, -200),
            (200, 3, 210, 7, 3.5),
            id="fee-once",
        ),
        pytest.param(
            [85000],
            [(20300, 300), (60128, 128)],
            80100,
            (80428, 4572),
            (80428, 428, 80100, -756, -0.94),
            id="fee-inside-the-price",
        ),
    ],
)
def test_a_purchase_debits_its_account_and_profits_the_worth_less_price_and_fee(
    main_user, incomes, purchases, worth_price, expected_account, expected_saving
):
    with quiet_build(main_user):
        account = AccountFactory(title="IB")
        saving_type = SavingTypeFactory(title="VALL")
        for price in incomes:
            IncomeFactory(account=account, price=price)
    for price, fee in purchases:
        SavingFactory(account=account, saving_type=saving_type, price=price, fee=fee)
    worth(saving_type, worth_price)

    actual_account = _account_balance(account)
    assert (actual_account.expenses, actual_account.balance) == expected_account

    saving = balance(saving_type)
    assert (
        saving.incomes,
        saving.fee,
        saving.market_value,
        saving.profit_sum,
        saving.profit_proc,
    ) == expected_saving


def test_finbee_fee_only_rows_paid_from_two_accounts(main_user):
    with quiet_build(main_user):
        seb = AccountFactory(title="SEB")
        revolut = AccountFactory(title="Revolut")
        finbee = SavingTypeFactory(title="Finbee")
        IncomeFactory(account=seb, price=5000)
        IncomeFactory(account=revolut, price=5000)
    SavingFactory(account=seb, saving_type=finbee, price=1000, fee=0)
    SavingFactory(account=seb, saving_type=finbee, price=0, fee=100)
    SavingFactory(account=revolut, saving_type=finbee, price=0, fee=100)
    worth(finbee, 1200)

    assert _account_balance(seb).balance == 4000
    assert _account_balance(revolut).balance == 5000

    saving = balance(finbee)
    assert saving.incomes == 1000
    assert saving.fee == 200
    assert saving.profit_sum == 0
    assert saving.profit_proc == 0.0


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


def test_saving_a_saving_type_leaves_every_balance_unchanged(main_user):
    with quiet_build(main_user):
        account = AccountFactory(title="IB")
        saving_type = SavingTypeFactory(title="VALL")
        SavingFactory(account=account, saving_type=saving_type, price=200, fee=3)
        worth(saving_type, 210)
    accounts, savings = _table(AccountBalance), _table(SavingBalance)

    saving_type.title = "VALL renamed"
    saving_type.save()

    assert _table(AccountBalance) == accounts
    assert _table(SavingBalance) == savings


def test_fee_source_does_not_change_the_saving_balance(main_user):
    balances = {}
    for title, fee_source in (
        ("A", SavingType.FeeSource.INVESTMENT),
        ("B", SavingType.FeeSource.ACCOUNT),
    ):
        saving_type = SavingTypeFactory(title=title, fee_source=fee_source)
        SavingFactory(saving_type=saving_type, price=200, fee=3)
        SavingFactory(saving_type=saving_type, price=0, fee=1)
        worth(saving_type, 210)
        balances[title] = (
            SavingBalance.objects.filter(saving_type=saving_type)
            .order_by("year")
            .values(*[f for f in SAVING_FIELDS if f != "latest_check"])
        )

    assert len(balances["A"]) == 2
    assert list(balances["A"]) == list(balances["B"])


def test_switching_a_types_fee_source_re_syncs_its_account(main_user):
    with quiet_build(main_user):
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
    with quiet_build(main_user):
        mine = SavingTypeFactory(title="My VALL")
        SavingFactory(account=AccountFactory(title="Mine"), saving_type=mine)
    assert _account_balance(theirs).expenses == 909
    # a re-sync of their journal would put 909 back
    AccountBalance.objects.filter(account=theirs).update(expenses=1)
    sync = mocker.spy(balance_sources, "sync_accounts")

    mine.fee_source = SavingType.FeeSource.ACCOUNT
    mine.save()

    assert [call.args[0] for call in sync.call_args_list] == [main_user]
    assert _account_balance(theirs).expenses == 1


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
    worth(fund, 310)
    # last, so a signal it fails to send is not covered by a later one
    SavingChangeFactory(from_account=finbee, to_account=fund, price=100, fee=5)
    accounts, savings = _table(AccountBalance), _table(SavingBalance)

    balance_sources.sync_accounts(user=main_user)
    balance_sources.sync_savings(user=main_user)

    assert _table(AccountBalance) == accounts
    assert _table(SavingBalance) == savings


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
        lambda user: balance_sources.sync_accounts(user=user),
    ],
    ids=["expenses", "re-sync"],
)
def test_query_count_does_not_grow_with_both_fee_sources(main_user, run):
    with quiet_build(main_user):
        _purchases_of_both_fee_sources(2)
    two = count_queries(lambda: run(main_user))
    SavingType.objects.all().delete()

    with quiet_build(main_user):
        _purchases_of_both_fee_sources(4)

    assert count_queries(lambda: run(main_user)) == two
