import pytest

from ...accounts.factories import AccountBalanceFactory
from ...accounts.models import AccountBalance
from ..lib import utils as T


@pytest.fixture()
def arr():
    return ([
        {'key1': 1, 'key2': 2.0, 'key3': 'a'},
        {'key1': 2, 'key2': 4.0, 'key3': 'b'},
    ])


def test_sum_column(arr):
    actual = T.sum_col(arr, 'key1')

    assert 3 == actual


@pytest.mark.django_db
def test_sum_column_query_set():
    AccountBalanceFactory()

    qs = AccountBalance.objects.all()

    actual = T.sum_col(qs, 'past')

    assert 1 == actual


def test_sum_all(arr):
    actual = T.sum_all(arr)

    assert 3 == actual['key1']
    assert 6.0 == actual['key2']


def test_sum_all_empty_list():
    actual = T.sum_all([])

    assert {} == actual


@pytest.mark.django_db
def test_sum_all_query_set():
    AccountBalanceFactory()

    qs = AccountBalance.objects.all()

    actual = T.sum_all(qs)

    assert 1 == actual['past']
