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
    assert actual.past == 1.0
    assert actual.incomes == 6.75
    assert actual.expenses == 6.5
    assert actual.balance == 1.25
    assert actual.have == 0.20
    assert actual.delta == -1.05


def test_account_balance_str():
    actual = AccountBalanceFactory.build()

    assert str(actual) == 'Account1'


@pytest.mark.django_db
def test_account_balance_items():
    AccountBalanceFactory(year=1998)
    AccountBalanceFactory(year=1999)
    AccountBalanceFactory(year=2000)

    actual = AccountBalance.objects.items(1999)

    assert len(actual) == 1


@pytest.mark.django_db
def test_account_balance_queries(django_assert_num_queries):
    a1 = AccountFactory(title='a1')
    a2 = AccountFactory(title='a2')

    AccountBalanceFactory(account=a1)
    AccountBalanceFactory(account=a2)

    with django_assert_num_queries(1) as captured:
        q = AccountBalance.objects.items()
        for i in q:
            title = i['title']
