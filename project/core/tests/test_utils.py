from datetime import datetime
from types import SimpleNamespace

import pytest
from mock import patch

from ...accounts.factories import AccountBalanceFactory
from ...accounts.models import AccountBalance
from ...journals.factories import JournalFactory
from ...users.factories import UserFactory
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


@pytest.mark.django_db
@pytest.mark.disable_get_user_patch
@patch('project.core.lib.utils.CrequestMiddleware')
@patch('project.core.lib.utils.get_user')
def test_get_journal_not_found_in_session(mck_user, mck_journal):
    u = UserFactory()
    j1 = JournalFactory(user=UserFactory(username='X'))
    j2 = JournalFactory(user=u)

    mck_user.return_value = u
    mck_journal.get_request.return_value = SimpleNamespace(session={'journal': None})

    actual = T.get_journal()

    assert actual == j2


@pytest.mark.django_db
@pytest.mark.disable_get_user_patch
@patch('project.core.lib.utils.CrequestMiddleware')
def test_get_journal_from_session(mck_journal):
    mck_journal.get_request.return_value = SimpleNamespace(session={'journal': 66})

    actual = T.get_journal()

    assert actual == 66
