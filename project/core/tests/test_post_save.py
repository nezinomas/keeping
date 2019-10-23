import pytest
from mock import patch

from ...accounts.factories import AccountFactory, AccountBalanceFactory
from ...accounts.models import AccountBalance
from ..lib import post_save as T

pytestmark = pytest.mark.django_db


def test_account_list_full():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    actual = T._accounts()

    assert {'A1': a1.id, 'A2': a2.id} == actual


def test_account_list_one():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    actual = T._accounts(a1.id)

    assert {'A1': a1.id} == actual


@patch('project.core.lib.post_save._account_stats')
def test_insert(_mock):
    a1 = AccountFactory(title='A1')
    _mock.return_value = [{'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    T.post_save_account_stats(a1.id)

    actual = AccountBalance.objects.all()

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 'A1' == actual.account.title
    assert 2.0 == actual.balance
    assert 1999 == actual.year


@patch('project.core.lib.post_save._account_stats')
def test_update(_mock):
    a1 = AccountFactory(title='A1')
    AccountBalanceFactory(account=a1)

    _mock.return_value = [{'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    T.post_save_account_stats(a1.id)

    actual = AccountBalance.objects.all()

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 'A1' == actual.account.title
    assert 2.0 == actual.balance
    assert 1.0 == actual.past
    assert 6.75 == actual.incomes
    assert 6.5 == actual.expenses
    assert 0.20 == actual.have
    assert -1.05 == actual.delta
