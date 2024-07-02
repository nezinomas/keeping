from datetime import datetime
from types import SimpleNamespace

import pytest
from mock import patch

from ...accounts.factories import AccountBalanceFactory
from ...accounts.models import AccountBalance
from ..lib import utils as T



@patch('project.core.lib.utils.CrequestMiddleware')
def test_get_request_kwargs(mck):
    mck.get_request.return_value = SimpleNamespace(resolver_match=SimpleNamespace(kwargs={'Foo': 'Boo'}))
    actual = T.get_request_kwargs('Foo')
    assert actual == 'Boo'


@patch('project.core.lib.utils.CrequestMiddleware')
def test_get_request_kwargs_no_name(mck):
    mck.get_request.return_value = SimpleNamespace(resolver_match=SimpleNamespace(kwargs={}))
    actual = T.get_request_kwargs('Foo')
    assert not actual


def test_total_row_objects():
    data = [
        SimpleNamespace(x=111, A=1, B=2),
        SimpleNamespace(x=222, A=1, B=2),
    ]
    actual = T.total_row(data, fields=["A", "B"])

    assert actual == {
        "A": 2,
        "B": 4,
    }


def test_total_row_no_data():
    actual = T.total_row([], fields=["A", "B"])

    assert actual == {
        "A": 0,
        "B": 0,
    }
