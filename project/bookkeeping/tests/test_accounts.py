import pytest

from ..lib.get_accounts import GetData as Accounts

pytestmark = pytest.mark.django_db


def test_accounts(_accounts):
    actual = Accounts().accounts

    expect = {'Account1': 0, 'Account2': 0}

    assert expect == actual
