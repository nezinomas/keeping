from datetime import datetime
from decimal import Decimal

import pytest

from ..services.accounts import AccountsServiceNew


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        {'year': 1999, 'incomes': Decimal('100'), 'id': 'X'},
        {'year': 2000, 'incomes': Decimal('200'), 'id': 'X'},
        {'year': 1999, 'incomes': Decimal('110'), 'id': 'Y'},
        {'year': 2000, 'incomes': Decimal('220'), 'id': 'Y'},
    ]

@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        {'year': 1999, 'expenses': Decimal('50'), 'id': 'X'},
        {'year': 2000, 'expenses': Decimal('100'), 'id': 'X'},
        {'year': 2000, 'expenses': Decimal('110'), 'id': 'Y'},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {'title': 'X', 'have': Decimal('10'), 'latest_check': datetime(2000, 1, 1)},
        {'title': 'Y', 'have': Decimal('20'), 'latest_check': datetime(2000, 1, 1)},
    ]


def test_table(incomes, expenses, have):
    actual = AccountsServiceNew(2000, incomes, expenses, have).table()

    expect = [
        {'id': 'X', 'past': 50.0, 'incomes': 200.0, 'expenses': 100.0, 'balance': 150.0, 'have': 10.0, 'delta': -140.0},
        {'id': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 110.0, 'balance': 220.0, 'have': 20.0, 'delta': -200.0},
    ]

    assert actual == expect


def test_table_have_empty(incomes, expenses):
    actual = AccountsServiceNew(2000, incomes, expenses).table()

    expect = [
        {'id': 'X', 'past': 50.0, 'incomes': 200.0, 'expenses': 100.0, 'balance': 150.0, 'have': 0.0, 'delta': -150.0},
        {'id': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 110.0, 'balance': 220.0, 'have': 0.0, 'delta': -220.0},
    ]

    assert actual == expect


def test_table_have_partial(incomes, expenses, have):
    actual = AccountsServiceNew(2000, incomes, expenses, have[:1]).table()

    expect = [
        {'id': 'X', 'past': 50.0, 'incomes': 200.0, 'expenses': 100.0, 'balance': 150.0, 'have': 10.0, 'delta': -140.0},
        {'id': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 110.0, 'balance': 220.0, 'have': 0.0, 'delta': -220.0},
    ]

    assert actual == expect
