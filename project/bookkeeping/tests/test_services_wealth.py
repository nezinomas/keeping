from types import SimpleNamespace

import pytest

from ...accounts.factories import AccountBalanceFactory
from ...pensions.factories import PensionBalanceFactory
from ...savings.factories import SavingBalanceFactory
from ..services.wealth import Wealth, Data

pytestmark = pytest.mark.django_db


def test_data_service_empty_db():
    obj = Data(1999)

    assert obj.year == 1999
    assert obj.account_balance == 0
    assert obj.saving_balance == 0
    assert obj.pension_balance == 0


def test_data_service_account_balance():
    AccountBalanceFactory()
    AccountBalanceFactory()

    obj = Data(1999)

    assert obj.account_balance == 250


def test_data_service_saving_balance():
    SavingBalanceFactory()
    SavingBalanceFactory()

    obj = Data(1999)

    assert obj.saving_balance == 50


def test_data_service_pension_balance():
    PensionBalanceFactory()
    PensionBalanceFactory()

    obj = Data(1999)

    assert obj.pension_balance == 50


def test_data():
    obj = Wealth(
        data=SimpleNamespace(
            year=1111, account_balance=1, saving_balance=2, pension_balance=4
        )
    )

    assert obj.data.year == 1111
    assert obj.data.account_balance == 1
    assert obj.data.saving_balance == 2
    assert obj.data.pension_balance == 4


def test_money():
    obj = Wealth(
        data=SimpleNamespace(account_balance=1, saving_balance=2, pension_balance=4)
    )
    actual = obj.money

    assert actual == 3


def test_wealth():
    obj = Wealth(
        data=SimpleNamespace(account_balance=1, saving_balance=2, pension_balance=4)
    )
    actual = obj.wealth

    assert actual == 7
