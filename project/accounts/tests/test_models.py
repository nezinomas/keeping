import pytest

from ..factories import AccountFactory


def test_str():
    actual = AccountFactory.build()

    assert 'Account1' == str(actual)
