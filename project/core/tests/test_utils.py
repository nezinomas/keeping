from datetime import datetime

import pytest

from ...accounts.factories import AccountBalanceFactory
from ...accounts.models import AccountBalance
from ..lib import utils as T


@pytest.fixture()
def _arr():
    return ([
        {'key1': 1, 'key2': 2.0, 'key3': 'a'},
        {'key1': 2, 'key2': 4.0, 'key3': 'b'},
    ])


def test_sum_column(_arr):
    actual = T.sum_col(_arr, 'key1')

    assert actual == 3


@pytest.mark.django_db
def test_sum_column_query_set():
    AccountBalanceFactory()

    qs = AccountBalance.objects.all()

    actual = T.sum_col(qs, 'past')

    assert actual == 1


def test_sum_all(_arr):
    actual = T.sum_all(_arr)

    assert actual['key1'] == 3
    assert actual['key2'] == 6.0


def test_sum_all_empty_list():
    actual = T.sum_all([])

    assert {} == actual


def test_sum_all_with_datetime():
    arr = [{'a': datetime(2000, 1, 1)}, {'a': datetime(1999, 2, 1)}]
    T.sum_all(arr)


@pytest.mark.django_db
def test_sum_all_query_set():
    AccountBalanceFactory()

    qs = AccountBalance.objects.all()

    actual = T.sum_all(qs)

    assert actual['past'] == 1
