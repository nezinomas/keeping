import pytest

from ....accounts.tests.factories import AccountBalanceFactory
from ....pensions.tests.factories import PensionBalanceFactory
from ....savings.tests.factories import SavingBalanceFactory, SavingTypeFactory
from ...services.wealth.dtos import WealthDto
from ...services.wealth.presenters import WealthPresenter
from ...services.wealth.providers import WealthDataProvider
from ..helper import quiet_build, stale_fund
from ..signals.helpers import buy, sell, worth

pytestmark = pytest.mark.django_db


def _wealth(user, account_balance=0):
    return WealthDataProvider(user, 1999).get_wealth_data(account_balance)


def _saving_balance(dto):
    return dto.saving_balance


def _pension_balance(dto):
    return dto.pension_balance


@pytest.mark.parametrize(
    "builds, field, total",
    [
        # an empty year reads the database's default, an int zero
        pytest.param([], _saving_balance, 0, id="funds-empty"),
        pytest.param([], _pension_balance, 0, id="pensions-empty"),
        pytest.param([SavingBalanceFactory] * 2, _saving_balance, 50, id="funds"),
        pytest.param([PensionBalanceFactory] * 2, _pension_balance, 50, id="pensions"),
        pytest.param(
            [
                lambda: PensionBalanceFactory(market_value=100, sold_since_check=40),
                lambda: PensionBalanceFactory(market_value=25),
            ],
            _pension_balance,
            25,
            id="pensions-a-stale-worth-as-zero",
        ),
    ],
)
def test_provider_sums_each_balance(main_user, builds, field, total):
    for build in builds:
        build()

    balance = field(_wealth(main_user))

    assert (balance, type(balance)) == (total, int)


def test_provider_counts_the_accounts_total_it_is_handed(main_user):
    # the year's balance row is not what counts: the total handed in is
    AccountBalanceFactory()

    assert _wealth(main_user, account_balance=7).account_balance == 7


@pytest.mark.parametrize(
    "figure, total",
    [
        pytest.param(lambda wealth: wealth.money, 3, id="money"),
        pytest.param(lambda wealth: wealth.wealth, 7, id="wealth"),
    ],
)
def test_presenter_money_leaves_out_the_pensions_and_wealth_counts_them(figure, total):
    dto = WealthDto(account_balance=1, saving_balance=2, pension_balance=4)

    assert figure(WealthPresenter(dto)) == total


def _fund_bought_in_1999(closed=None):
    fund = SavingTypeFactory(title="Fund", closed=closed)
    buy(fund, 100000)
    return fund


def test_provider_closed_fund_with_a_sell_counts_no_worth(main_user):
    with quiet_build(main_user):
        fund = _fund_bought_in_1999(closed=1999)
        sell(fund, 90000)
        worth(fund, 95000)

    assert _wealth(main_user).saving_balance == 0


def test_provider_fund_without_a_close_counts_its_worth(main_user):
    with quiet_build(main_user):
        fund = _fund_bought_in_1999()
        worth(fund, 95000)

    assert _wealth(main_user).saving_balance == 95000


@pytest.mark.parametrize("kind", ["funds", "pensions"])
def test_provider_counts_a_fund_with_a_stale_worth_as_zero(main_user, kind):
    with quiet_build(main_user):
        stale_fund(kind=kind)

    assert _wealth(main_user).saving_balance == 0


def test_provider_counts_a_fresh_worth_after_the_sell(main_user):
    with quiet_build(main_user):
        fund = stale_fund()
        worth(fund, 60000)

    assert _wealth(main_user).saving_balance == 60000
