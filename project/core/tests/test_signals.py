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
def test_account_list_full(mck, get_user):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    obj = T.SignalBase(None)
    obj.model_types = Account

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=None):
        actual = obj._get_accounts()

        assert {'A1': a1.id, 'A2': a2.id} == actual


@patch('project.core.signals.SignalBase._update_or_create')
def test_account_list_one(mock_init, get_user):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    obj = T.SignalBase(None)
    obj.model_types = Account

    func = 'project.core.signals.SignalBase._get_id'
    with patch(func, return_value=[a1.id]):
        actual = obj._get_accounts()

        assert {'A1': a1.id} == actual


@patch('project.core.signals.SignalBase._get_stats')
def test_account_insert(_mock, get_user):
    a1 = AccountFactory(title='A1')
    _mock.return_value = [
        {'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    instance = SimpleNamespace(account_id=a1.id)
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = list(actual)[0]

    assert actual['title'] == 'A1'
    assert actual['balance'] == 2.0
    assert actual['year'] == 1999


@patch('project.core.signals.SignalBase._get_stats')
def test_account_insert_instance_account_id_not_set(_mock, get_user):
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')
    _mock.return_value = [
        {'title': 'A1', 'id': a1.id, 'balance': 2.0},
        {'title': 'A2', 'id': a2.id, 'balance': 4.0},
    ]

    instance = SimpleNamespace()
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 2

    actual = list(actual)

    assert actual[0]['title'] == 'A1'
    assert actual[0]['balance'] == 2.0
    assert actual[0]['year'] == 1999

    assert actual[1]['title'] == 'A2'
    assert actual[1]['balance'] == 4.0
    assert actual[1]['year'] == 1999


@patch('project.core.signals.SignalBase._get_stats')
def test_account_update(_mock, get_user):
    a1 = AccountFactory(title='A1')
    AccountBalanceFactory(account=a1)

    _mock.return_value = [{'title': 'A1', 'id': a1.id, 'balance': 2.0}]

    instance = SimpleNamespace(account_id=a1.id)
    T.post_save_account_stats(instance=instance)

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = list(actual)[0]

    assert actual['title'] == 'A1'
    assert actual['balance'] == 2.0
    assert actual['past'] == 1.0
    assert actual['incomes'] == 6.75
    assert actual['expenses'] == 6.5
    assert actual['have'] == 0.20
    assert actual['delta'] == -1.05


# ----------------------------------------------------------------------------
#                                                      post_save_savings_stats
# ----------------------------------------------------------------------------
@patch('project.core.signals.SignalBase._update_or_create')
def test_saving_list_full(_mock, get_user):
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
def test_saving_list_one(_mock, get_user):
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
def test_saving_list_full_without_closed(_mock, get_user):
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
def test_saving_list_without_closed(_mock, get_user):
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
def test_saving_insert(_mock, get_user):
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

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1

    actual = list(actual)[0]

    assert actual['year'] == 1999
    assert actual['title'] == 'S1'
    assert actual['past_amount'] == 2.0
    assert actual['past_fee'] == 2.1
    assert actual['fees'] == 2.2
    assert actual['invested'] == 2.3
    assert actual['incomes'] == 2.4
    assert actual['market_value'] == 2.5
    assert actual['profit_incomes_proc'] == 2.6
    assert actual['profit_incomes_sum'] == 2.7
    assert actual['profit_invested_proc'] == 2.8
    assert actual['profit_invested_sum'] == 2.9


@patch('project.core.signals.SignalBase._get_stats')
def test_saving_insert_instance_saving_id_not_set(_mock, get_user):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2')
    _mock.return_value = [
        {'title': 'S1', 'id': s1.id, 'past_amount': 2.0},
        {'title': 'S2', 'id': s2.id, 'past_amount': 4.0},
    ]

    instance = SimpleNamespace()
    T.post_save_saving_stats(instance=instance)

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 2

    actual = list(actual)

    assert actual[0]['title'] == 'S1'
    assert actual[0]['past_amount'] == 2.0
    assert actual[0]['year'] == 1999

    assert actual[1]['title'] == 'S2'
    assert actual[1]['past_amount'] == 4.0
    assert actual[1]['year'] == 1999


@patch('project.core.signals.SignalBase._get_stats')
def test_saving_update(_mock, get_user):
    s1 = SavingTypeFactory(title='S1')
    SavingBalanceFactory(saving_type=s1)

    _mock.return_value = [{'title': 'S1', 'id': s1.id, 'past_amount': 22.0}]

    instance = SimpleNamespace(saving_id=s1.id)
    T.post_save_saving_stats(instance=instance)

    actual = SavingBalance.objects.year(1999)

    assert actual.count() == 1

    actual = list(actual)[0]

    assert actual['title'] == 'S1'
    assert actual['past_amount'] == 22.0
