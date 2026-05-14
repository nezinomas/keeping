import pytest
from django.utils.translation import override

from ....accounts.tests.factories import AccountBalanceFactory
from ....pensions.tests.factories import PensionBalanceFactory
from ....savings.tests.factories import SavingBalanceFactory
from ...services.wealth.dtos import WealthDto
from ...services.wealth.presenters import WealthPresenter, build_context
from ...services.wealth.providers import WealthDataProvider

pytestmark = pytest.mark.django_db


def test_provider_empty_db(main_user):
    obj = WealthDataProvider(main_user, 1999).get_wealth_data()

    assert obj.account_balance == 0
    assert obj.saving_balance == 0
    assert obj.pension_balance == 0


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
