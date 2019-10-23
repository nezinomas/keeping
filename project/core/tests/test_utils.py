import pytest

from ..lib import utils as T


@pytest.fixture()
def arr():
    return ([
        {'key1': 1, 'key2': 2.0},
        {'key1': 2, 'key2': 4.0},
    ])


def test_sum_column(arr):
    actual = T.sum_col(arr, 'key1')

    assert 3 == actual


def test_sum_all(arr):
    actual = T.sum_all(arr)

    assert 3 == actual['key1']
    assert 6.0 == actual['key2']


def test_sum_all_empty_list():
    actual = T.sum_all([])

    assert {} == actual
