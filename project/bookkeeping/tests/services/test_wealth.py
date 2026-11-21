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


def _wealth(user):
    return WealthDataProvider(user, 1999).get_wealth_data()


def test_provider_empty_year_is_the_database_default_zero(main_user):
    obj = _wealth(main_user)

    balances = (obj.account_balance, obj.saving_balance, obj.pension_balance)

    assert [(balance, type(balance)) for balance in balances] == [(0, int)] * 3


@pytest.mark.parametrize(
    "factory, field, total",
    [
        pytest.param(
            AccountBalanceFactory, lambda dto: dto.account_balance, 250, id="accounts"
        ),
        pytest.param(
            SavingBalanceFactory, lambda dto: dto.saving_balance, 50, id="funds"
        ),
        pytest.param(
            PensionBalanceFactory, lambda dto: dto.pension_balance, 50, id="pensions"
        ),
    ],
)
def test_provider_sums_each_balance(main_user, factory, field, total):
    factory()
    factory()

    assert field(_wealth(main_user)) == total


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


def test_provider_counts_a_pension_balance_with_a_stale_worth_as_zero(main_user):
    PensionBalanceFactory(market_value=100, sold_since_check=40)
    PensionBalanceFactory(market_value=25)

    assert _wealth(main_user).pension_balance == 25


def test_provider_counts_a_fresh_worth_after_the_sell(main_user):
    with quiet_build(main_user):
        fund = stale_fund()
        worth(fund, 60000)

    assert _wealth(main_user).saving_balance == 60000
