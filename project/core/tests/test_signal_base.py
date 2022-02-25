from types import SimpleNamespace

import pytest
from django.core.exceptions import ObjectDoesNotExist
from mock import patch

from ...accounts.factories import AccountFactory
from ..conf import Conf
from ..signals_base import SignalBase


@pytest.fixture
def _conf():
    _hooks = {
        'incomes.Income': [
             {
                 'method': 'incomes',
                 'category': 'account',
                 'balance_field': 'incomes',
             }, {
                 'method': 'xxx',
                 'category': 'xxx',
                 'balance_field': 'xxx'
            }
        ]
    }

    return Conf(
        sender=SimpleNamespace(
            __module__='project.incomes.models',
            __name__ = 'Income'
        ),
        instance=SimpleNamespace(
            account = SimpleNamespace(pk = 1),
            old_values = {'account': 1}
        ),
        created=False,
        signal='any',
        tbl_categories='Categories_model',
        tbl_balance='Balance_model',
        hooks=_hooks,
        balance_class_method='accounts',
        balance_model_fk_field='account_id'
    )


@patch('project.core.signals_base.SignalBase._tbl_balance_field_update')
def test_no_hooks(mck, _conf):
    _conf.hooks.pop('incomes.Income')

    SignalBase(_conf)

    assert mck.call_count == 0


@patch('project.core.signals_base.SignalBase._tbl_balance_field_update')
def test_created_fail(mck, _conf):
    _conf.created = True
    mck.side_effect = ObjectDoesNotExist

    SignalBase(_conf)

    assert mck.call_count == 1


@patch('project.core.signals_base.SignalBase._tbl_balance_field_update')
def test_created(mck, _conf):
    _conf.created = True

    SignalBase(_conf)

    assert mck.call_count == 2


@patch('project.core.signals_base.SignalBase._tbl_balance_field_update')
def test_update_when_category_changed(mck, _conf):
    del _conf.hooks['incomes.Income'][1]
    _conf.old_values['account'] = 2

    SignalBase(_conf)

    assert mck.call_count == 2


@patch('project.core.signals_base.SignalBase._tbl_balance_field_update')
def test_delete_signal(mck, _conf):
    _conf.signal = 'delete'

    SignalBase(_conf)

    assert mck.call_count == 2
