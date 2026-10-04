from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils.translation import override

from ....accounts.tests.factories import AccountBalanceFactory
from ....pensions.tests.factories import PensionBalanceFactory
from ....savings.tests.factories import (
    SavingBalanceFactory,
    SavingFactory,
    SavingTypeFactory,
)
from ....transactions.tests.factories import SavingCloseFactory
from ...services.wealth.dtos import WealthDto
from ...services.wealth.presenters import WealthPresenter, build_context
from ...services.wealth.providers import WealthDataProvider
from ..factories import SavingWorthFactory

pytestmark = pytest.mark.django_db

WORTH_DATE = datetime(1999, 12, 31, 12, tzinfo=ZoneInfo("Europe/Vilnius"))


def test_provider_empty_db(main_user):
    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.account_balance == 0
    assert obj.saving_balance == 0
    assert obj.pension_balance == 0


def test_provider_empty_year_is_the_database_default_not_a_float(main_user):
    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert type(obj.account_balance) is int
    assert type(obj.saving_balance) is int
    assert type(obj.pension_balance) is int


def test_provider_account_balance(main_user):
    AccountBalanceFactory()
    AccountBalanceFactory()

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.account_balance == 250


def test_provider_saving_balance(main_user):
    SavingBalanceFactory()
    SavingBalanceFactory()

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.saving_balance == 50


def test_provider_pension_balance(main_user):
    PensionBalanceFactory()
    PensionBalanceFactory()

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.pension_balance == 50


def test_presenter_money():
    dto = WealthDto(account_balance=1, saving_balance=2, pension_balance=4)
    actual = WealthPresenter(dto).money

    assert actual == 3


def test_presenter_wealth():
    dto = WealthDto(account_balance=1, saving_balance=2, pension_balance=4)
    actual = WealthPresenter(dto).wealth

    assert actual == 7


def test_build_context():
    with override("en"):
        dto = WealthDto(account_balance=1, saving_balance=2, pension_balance=4)
        actual = build_context(dto)

        assert "data" in actual
        assert actual["data"]["title"] == ["Money", "Wealth"]
        assert actual["data"]["data"] == [3, 7]


def _fund_bought_in_1999(closed=None):
    fund = SavingTypeFactory(title="Fund", closed=closed)
    SavingFactory(saving_type=fund, price=100000, fee=0, date=date(1999, 1, 1))
    return fund


def test_provider_closed_fund_with_a_sell_counts_no_worth(main_user):
    fund = _fund_bought_in_1999(closed=1999)
    SavingCloseFactory(from_account=fund, price=90000, fee=0, date=date(1999, 6, 1))
    SavingWorthFactory(saving_type=fund, price=95000, date=WORTH_DATE)

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.saving_balance == 0


def test_provider_fund_without_a_close_counts_its_worth(main_user):
    fund = _fund_bought_in_1999()
    SavingWorthFactory(saving_type=fund, price=95000, date=WORTH_DATE)

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.saving_balance == 95000


def _stale_fund_bought_in_1999(kind="funds"):
    fund = SavingTypeFactory(title="Fund", type=kind)
    SavingFactory(saving_type=fund, price=100000, fee=0, date=date(1999, 1, 1))
    SavingWorthFactory(
        saving_type=fund,
        price=100000,
        date=datetime(1999, 3, 1, 12, tzinfo=ZoneInfo("Europe/Vilnius")),
    )
    SavingCloseFactory(from_account=fund, price=40000, fee=0, date=date(1999, 6, 1))
    return fund


def test_provider_counts_a_fund_with_a_stale_worth_as_zero(main_user):
    _stale_fund_bought_in_1999()

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.saving_balance == 0


def test_provider_counts_a_stale_pension_type_as_zero(main_user):
    _stale_fund_bought_in_1999(kind="pensions")

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.saving_balance == 0


def test_provider_counts_a_pension_balance_with_a_stale_worth_as_zero(main_user):
    PensionBalanceFactory(market_value=100, sold_since_check=40)
    PensionBalanceFactory(market_value=25)

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.pension_balance == 25


def test_provider_counts_a_fresh_worth_after_the_sell(main_user):
    fund = _stale_fund_bought_in_1999()
    SavingWorthFactory(saving_type=fund, price=60000, date=WORTH_DATE)

    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.saving_balance == 60000
