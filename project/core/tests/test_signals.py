import pytest
from mock import patch
from types import SimpleNamespace
from ...accounts.factories import AccountFactory, AccountBalanceFactory
from ...accounts.models import AccountBalance
from .. import signals as T

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


@patch('project.core.signals._account_stats')
def test_insert(_mock, mock_crequest):
    a1 = AccountFactory(title='A1')
    _mock.return_value = [
        {'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    instance = SimpleNamespace(account_id=a1.id)
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.all()

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 'A1' == actual.account.title
    assert 2.0 == actual.balance
    assert 1999 == actual.year


@patch('project.core.signals._account_stats')
def test_insert_instance_account_id_not_set(_mock, mock_crequest):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')
    _mock.return_value = [
        {'title': 'A1', 'id': a1.id, 'balance': 2.0},
        {'title': 'A2', 'id': a2.id, 'balance': 4.0},
    ]

    instance = SimpleNamespace()
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.all()

    assert 2 == actual.count()

    actual = list(actual)

    assert 'A1' == actual[0].account.title
    assert 2.0 == actual[0].balance
    assert 1999 == actual[0].year

    assert 'A2' == actual[1].account.title
    assert 4.0 == actual[1].balance
    assert 1999 == actual[1].year


@patch('project.core.signals._account_stats')
def test_update(_mock, mock_crequest):
    a1 = AccountFactory(title='A1')
    AccountBalanceFactory(account=a1)

    _mock.return_value = [{'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    instance = SimpleNamespace(account_id=a1.id)
    T.post_save_account_stats(instance=instance)

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
