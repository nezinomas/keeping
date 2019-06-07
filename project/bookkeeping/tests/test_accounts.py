import pytest

from ...accounts.factories import AccountFactory
from ..lib.accounts import Accounts

pytestmark = pytest.mark.django_db


def test_accounts_list(_accounts):
    actual = Accounts().account_list

    expect = ['Account1', 'Account2']

    assert expect == actual


def test_accounts_dictionary(_accounts):
    actual = Accounts().account_dictionary

    expect = {'Account1': 0, 'Account2': 0}

    assert expect == actual
