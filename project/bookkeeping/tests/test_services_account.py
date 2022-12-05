from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from ..services.accounts import AccountsServiceNew


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        {'year': 1999, 'incomes': Decimal('100'), 'title': 'X'},
        {'year': 2000, 'incomes': Decimal('200'), 'title': 'X'},
        {'year': 1999, 'incomes': Decimal('110'), 'title': 'Y'},
        {'year': 2000, 'incomes': Decimal('220'), 'title': 'Y'},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        {'year': 1999, 'expenses': Decimal('50'), 'title': 'X'},
        {'year': 2000, 'expenses': Decimal('100'), 'title': 'X'},
        {'year': 2000, 'expenses': Decimal('110'), 'title': 'Y'},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {'title': 'X', 'have': Decimal('10'), 'latest_check': datetime(2000, 1, 1)},
        {'title': 'Y', 'have': Decimal('20'), 'latest_check': datetime(2000, 1, 1)},
    ]


def test_table(incomes, expenses, have):
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=have)
    actual = AccountsServiceNew(data).table()

    expect = [
        {'title': 'X', 'past': 50.0, 'incomes': 200.0, 'expenses': 100.0, 'balance': 150.0, 'have': 10.0, 'delta': -140.0},
        {'title': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 110.0, 'balance': 220.0, 'have': 20.0, 'delta': -200.0},
    ]

    assert actual == expect


def test_table_have_empty(incomes, expenses):
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=[])
    actual = AccountsServiceNew(data).table()

    expect = [
        {'title': 'X', 'past': 50.0, 'incomes': 200.0, 'expenses': 100.0, 'balance': 150.0, 'have': 0.0, 'delta': -150.0},
        {'title': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 110.0, 'balance': 220.0, 'have': 0.0, 'delta': -220.0},
    ]

    assert actual == expect


def test_table_have_partial(incomes, expenses, have):
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=have[:1])
    actual = AccountsServiceNew(data).table()

    expect = [
        {'title': 'X', 'past': 50.0, 'incomes': 200.0, 'expenses': 100.0, 'balance': 150.0, 'have': 10.0, 'delta': -140.0},
        {'title': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 110.0, 'balance': 220.0, 'have': 0.0, 'delta': -220.0},
    ]

    assert actual == expect


def test_table_incomes_empty(expenses):
    data = SimpleNamespace(year=2000, incomes=[], expenses=expenses, have=[])
    actual = AccountsServiceNew(data).table()

    expect = [
        {'title': 'X', 'past': -50.0, 'incomes': 0.0, 'expenses': 100.0, 'balance': -150.0, 'have': 0.0, 'delta': 150.0},
        {'title': 'Y', 'past': 0.0, 'incomes': 0.0, 'expenses': 110.0, 'balance': -110.0, 'have': 0.0, 'delta': 110.0},
    ]

    assert actual == expect


def test_table_expenses_empty(incomes):
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=[], have=[])
    actual = AccountsServiceNew(data).table()

    expect = [
        {'title': 'X', 'past': 100.0, 'incomes': 200.0, 'expenses': 0.0, 'balance': 300.0, 'have': 0.0, 'delta': -300.0},
        {'title': 'Y', 'past': 110.0, 'incomes': 220.0, 'expenses': 0.0, 'balance': 330.0, 'have': 0.0, 'delta': -330.0},
    ]

    assert actual == expect


def test_table_incomes_expenses_empty():
    data = SimpleNamespace(year=2000, incomes=[], expenses=[], have=[])
    actual = AccountsServiceNew(data).table()

    expect = []

    assert actual == expect


def test_table_only_have(have):
    data = SimpleNamespace(year=2000, incomes=[], expenses=[], have=have)
    actual = AccountsServiceNew(data).table()

    expect = [
        {'title': 'X', 'past': 0.0, 'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'have': 10.0, 'delta': 10.0},
        {'title': 'Y', 'past': 0.0, 'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'have': 20.0, 'delta': 20.0},
    ]

    assert actual == expect
