from types import SimpleNamespace

import pytest
from mock import patch

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import Account, AccountBalance
from ...savings.factories import SavingBalanceFactory, SavingTypeFactory
from ...savings.models import SavingBalance, SavingType
from .. import signals as T

pytestmark = pytest.mark.django_db


@patch('project.core.signals.SignalBase._update_or_create')
def test_account_list_full(mck, mock_crequest):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    obj = T.SignalBase(None)
    obj.model_types = Account

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=None):
        actual = obj._get_accounts()

        assert {'A1': a1.id, 'A2': a2.id} == actual


@patch('project.core.signals.SignalBase._update_or_create')
def test_account_list_one(mock_init, mock_crequest):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    obj = T.SignalBase(None)
    obj.model_types = Account

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=[a1.id]):
        actual = obj._get_accounts()

        assert {'A1': a1.id} == actual


@patch('project.core.signals.SignalBase._get_stats')
def test_account_insert(_mock, mock_crequest):
    a1 = AccountFactory(title='A1')
    _mock.return_value = [
        {'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    instance = SimpleNamespace(account_id=a1.id)
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 'A1' == actual['title']
    assert 2.0 == actual['balance']
    assert 1999 == actual['year']


@patch('project.core.signals.SignalBase._get_stats')
def test_account_insert_instance_account_id_not_set(_mock, mock_crequest):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')
    _mock.return_value = [
        {'title': 'A1', 'id': a1.id, 'balance': 2.0},
        {'title': 'A2', 'id': a2.id, 'balance': 4.0},
    ]

    instance = SimpleNamespace()
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.items(1999)

    assert 2 == actual.count()

    actual = list(actual)

    assert 'A1' == actual[0]['title']
    assert 2.0 == actual[0]['balance']
    assert 1999 == actual[0]['year']

    assert 'A2' == actual[1]['title']
    assert 4.0 == actual[1]['balance']
    assert 1999 == actual[1]['year']


@patch('project.core.signals.SignalBase._get_stats')
def test_account_update(_mock, mock_crequest):
    a1 = AccountFactory(title='A1')
    AccountBalanceFactory(account=a1)

    _mock.return_value = [{'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    instance = SimpleNamespace(account_id=a1.id)
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 'A1' == actual['title']
    assert 2.0 == actual['balance']
    assert 1.0 == actual['past']
    assert 6.75 == actual['incomes']
    assert 6.5 == actual['expenses']
    assert 0.20 == actual['have']
    assert -1.05 == actual['delta']


# ----------------------------------------------------------------------------
#                                                      post_save_savings_stats
# ----------------------------------------------------------------------------
@patch('project.core.signals.SignalBase._update_or_create')
def test_saving_list_full(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2')

    obj = T.SignalBase(None)
    obj.model_types = SavingType
    obj.year = 2000

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=None):
        actual = obj._get_accounts()

        assert {'S1': s1.id, 'S2': s2.id} == actual


@patch('project.core.signals.SignalBase._update_or_create')
def test_saving_list_one(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2')

    obj = T.SignalBase(None)
    obj.model_types = SavingType
    obj.year = 1999

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=[s1.id]):
        actual = obj._get_accounts()

        assert {'S1': s1.id} == actual


@patch('project.core.signals.SignalBase._update_or_create')
def test_saving_list_full_without_closed(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    obj = T.SignalBase(None)
    obj.model_types = SavingType
    obj.year = 1999

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=None):
        actual = obj._get_accounts()

        assert {'S1': s1.id} == actual


@patch('project.core.signals.SignalBase._update_or_create')
def test_saving_list_without_closed(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    obj = T.SignalBase(None)
    obj.model_types = SavingType
    obj.year = 1999

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=[s2.id]):
        actual = obj._get_accounts()

        assert {} == actual


@patch('project.core.signals.SignalBase._get_stats')
def test_saving_insert(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    _mock.return_value = [{
        'title': 'S1',
        'id': s1.id,
        'past_amount': 2.0,
        'past_fee': 2.1,
        'fees': 2.2,
        'invested': 2.3,
        'incomes': 2.4,
        'market_value': 2.5,
        'profit_incomes_proc': 2.6,
        'profit_incomes_sum': 2.7,
        'profit_invested_proc': 2.8,
        'profit_invested_sum': 2.9
    }]

    instance = SimpleNamespace(id=1)
    T.post_save_saving_stats(instance=instance)

    actual = SavingBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 1999 == actual['year']
    assert 'S1' == actual['title']
    assert 2.0 == actual['past_amount']
    assert 2.1 == actual['past_fee']
    assert 2.2 == actual['fees']
    assert 2.3 == actual['invested']
    assert 2.4 == actual['incomes']
    assert 2.5 == actual['market_value']
    assert 2.6 == actual['profit_incomes_proc']
    assert 2.7 == actual['profit_incomes_sum']
    assert 2.8 == actual['profit_invested_proc']
    assert 2.9 == actual['profit_invested_sum']


@patch('project.core.signals.SignalBase._get_stats')
def test_saving_insert_instance_saving_id_not_set(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2')
    _mock.return_value = [
        {'title': 'S1', 'id': s1.id, 'past_amount': 2.0},
        {'title': 'S2', 'id': s2.id, 'past_amount': 4.0},
    ]

    instance = SimpleNamespace()
    T.post_save_saving_stats(instance=instance)

    actual = SavingBalance.objects.items(1999)

    assert 2 == actual.count()

    actual = list(actual)

    assert 'S1' == actual[0]['title']
    assert 2.0 == actual[0]['past_amount']
    assert 1999 == actual[0]['year']

    assert 'S2' == actual[1]['title']
    assert 4.0 == actual[1]['past_amount']
    assert 1999 == actual[1]['year']


@patch('project.core.signals.SignalBase._get_stats')
def test_saving_update(_mock, mock_crequest):
    s1 = SavingTypeFactory(title='S1')
    SavingBalanceFactory(saving_type=s1)

    _mock.return_value = [{'title': 'S1', 'id': s1.id, 'past_amount': 22.0}]

    instance = SimpleNamespace(saving_id=s1.id)
    T.post_save_saving_stats(instance=instance)

    actual = SavingBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = list(actual)[0]

    assert 'S1' == actual['title']
    assert 22.0 == actual['past_amount']
