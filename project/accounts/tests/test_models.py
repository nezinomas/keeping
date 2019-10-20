import pytest

from ..factories import AccountBalanceFactory, AccountFactory
from ..models import AccountBalance


def test_str():
    actual = AccountFactory.build()

    assert 'Account1' == str(actual)


def test_account_balance_init():
    actual = AccountBalanceFactory.build()

    assert str(actual.account) == 'Account1'

    assert actual.year == 1999
    assert actual.incomes == 6.75
    assert actual.expenses == 6.5
    assert actual.delta == 0.25
    assert actual.have == 0.20
    assert actual.diff == 0.05


def test_account_balance_str():
    actual = AccountBalanceFactory.build()

    assert str(actual) == 'Account1'


@pytest.mark.django_db
def test_account_balance_items():
    AccountBalanceFactory(year=1998)
    AccountBalanceFactory(year=1999)
    AccountBalanceFactory(year=2000)

    actual = AccountBalance.objects.items(1999)

    assert len(actual) == 2

    actual = actual[1]

    assert str(actual.account) == 'Account1'
    assert actual.year == 1999
    assert actual.incomes == 6.75
    assert actual.expenses == 6.5
    assert actual.delta == 0.25
    assert actual.have == 0.20
    assert actual.diff == 0.05
