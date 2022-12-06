from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from ..services.accounts import AccountsServiceNew


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        {'year': 1999, 'incomes': Decimal('50'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('50'), 'id': 1},
        {'year': 2000, 'incomes': Decimal('100'), 'id': 1},
        {'year': 2000, 'incomes': Decimal('100'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('55'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('55'), 'id': 2},
        {'year': 2000, 'incomes': Decimal('110'), 'id': 2},
        {'year': 2000, 'incomes': Decimal('110'), 'id': 2},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        {'year': 1999, 'expenses': Decimal('25'), 'id': 1},
        {'year': 1999, 'expenses': Decimal('25'), 'id': 1},
        {'year': 2000, 'expenses': Decimal('50'), 'id': 1},
        {'year': 2000, 'expenses': Decimal('50'), 'id': 1},
        {'year': 2000, 'expenses': Decimal('55'), 'id': 2},
        {'year': 2000, 'expenses': Decimal('55'), 'id': 2},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {'id': 1, 'year': 1999, 'have': Decimal('10'), 'latest_check': datetime(2000, 1, 1)},
        {'id': 1, 'year': 2000, 'have': Decimal('15'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 2, 'year': 1999, 'have': Decimal('20'), 'latest_check': datetime(2000, 1, 1)},
        {'id': 2, 'year': 2000, 'have': Decimal('25'), 'latest_check': datetime(1999, 1, 1)},
    ]


def test_table(incomes, expenses, have):
    incomes.extend([
        {'year': 1997, 'incomes': Decimal('5'), 'id': 1},
        {'year': 1998, 'incomes': Decimal('15'), 'id': 1},
    ])
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=have)
    actual = AccountsServiceNew(data).table

    expect = [
        dict(
            id=1, year=1997, past=0.0, incomes=5.0, expenses=0.0, balance=5.0, have=0.0, delta=-5.0),
        dict(
            id=1, year=1998, past=5.0, incomes=15.0, expenses=0.0, balance=20.0, have=0.0, delta=-20.0),
        dict(
            id=1, year=1999, past=20.0, incomes=100.0, expenses=50.0, balance=70.0, have=10.0, delta=-60.0),
        dict(
            id=1, year=2000, past=70.0, incomes=200.0, expenses=100.0, balance=170.0, have=15.0, delta=-155.0),
        dict(
            id=2, year=1999, past=0.0, incomes=110.0, expenses=0.0, balance=110.0, have=20.0, delta=-90.0),
        dict(
            id=2, year=2000, past=110.0, incomes=220.0, expenses=110.0, balance=220.0, have=25.0, delta=-195.0),
    ]

    assert actual == expect


def test_table_have_empty(incomes, expenses):
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=[])
    actual = AccountsServiceNew(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=100.0, expenses=50.0, balance=50.0, have=0.0, delta=-50.0),
        dict(
            id=1, year=2000, past=50.0, incomes=200.0, expenses=100.0, balance=150.0, have=0.0, delta=-150.0),
        dict(
            id=2, year=1999, past=0.0, incomes=110.0, expenses=0.0, balance=110.0, have=0.0, delta=-110.0),
        dict(
            id=2, year=2000, past=110.0, incomes=220.0, expenses=110.0, balance=220.0, have=0.0, delta=-220.0),
    ]

    assert actual == expect


def test_table_incomes_empty(expenses):
    data = SimpleNamespace(year=2000, incomes=[], expenses=expenses, have=[])
    actual = AccountsServiceNew(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=0.0, expenses=50.0, balance=-50.0, have=0.0, delta=50.0),
        dict(
            id=1, year=2000, past=-50.0, incomes=0.0, expenses=100.0, balance=-150.0, have=0.0, delta=150.0),
        dict(
            id=2, year=2000, past=0.0, incomes=0.0, expenses=110.0, balance=-110.0, have=0.0, delta=110.0),
    ]

    assert actual == expect


def test_table_expenses_empty(incomes):
    data = SimpleNamespace(year=2000, incomes=incomes, expenses=[], have=[])
    actual = AccountsServiceNew(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=100.0, expenses=0.0, balance=100.0, have=0.0, delta=-100.0),
        dict(
            id=1, year=2000, past=100.0, incomes=200.0, expenses=0.0, balance=300.0, have=0.0, delta=-300.0),
        dict(
            id=2, year=1999, past=0.0, incomes=110.0, expenses=0.0, balance=110.0, have=0.0, delta=-110.0),
        dict(
            id=2, year=2000, past=110.0, incomes=220.0, expenses=0.0, balance=330.0, have=0.0, delta=-330.0),
    ]

    assert actual == expect


def test_table_incomes_expenses_empty():
    data = SimpleNamespace(year=2000, incomes=[], expenses=[], have=[])
    actual = AccountsServiceNew(data).table

    expect = []

    assert actual == expect


def test_table_only_have(have):
    data = SimpleNamespace(year=2000, incomes=[], expenses=[], have=have)
    actual = AccountsServiceNew(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=10.0, delta=10.0),
        dict(
            id=1, year=2000, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=15.0, delta=15.0),
        dict(
            id=2, year=1999, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=20.0, delta=20.0),
        dict(
            id=2, year=2000, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=25.0, delta=25.0),
    ]

    assert actual == expect


# def test_total_row(incomes, expenses, have):
#     data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=have)
#     actual = AccountsServiceNew(data).total

#     expect = {'past': 160.0, 'incomes': 420.0, 'expenses': 210.0, 'balance': 370.0, 'have': 30.0, 'delta': -340.0}

#     assert actual == expect


# def test_total_row_have_empty(incomes, expenses):
#     data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=[])
#     actual = AccountsServiceNew(data).total

#     expect = {'past': 160.0, 'incomes': 420.0, 'expenses': 210.0, 'balance': 370.0, 'have': 0.0, 'delta': -370.0}

#     assert actual == expect


# def test_total_row_have_partial(incomes, expenses, have):
#     data = SimpleNamespace(year=2000, incomes=incomes, expenses=expenses, have=have[:1])
#     actual = AccountsServiceNew(data).total

#     expect = {'past': 160.0, 'incomes': 420.0, 'expenses': 210.0, 'balance': 370.0, 'have': 10.0, 'delta': -360.0}

#     assert actual == expect


# def test_total_row_incomes_empty(expenses):
#     data = SimpleNamespace(year=2000, incomes=[], expenses=expenses, have=[])
#     actual = AccountsServiceNew(data).total

#     expect = {'past': -50.0, 'incomes': 0.0, 'expenses': 210.0, 'balance': -260.0, 'have': 0.0, 'delta': 260.0}

#     assert actual == expect


# def test_total_row_expenses_empty(incomes):
#     data = SimpleNamespace(year=2000, incomes=incomes, expenses=[], have=[])
#     actual = AccountsServiceNew(data).total

#     expect = {'past': 210.0, 'incomes': 420.0, 'expenses': 0.0, 'balance': 630.0, 'have': 0.0, 'delta': -630.0}

#     assert actual == expect


# def test_total_row_incomes_expenses_empty():
#     data = SimpleNamespace(year=2000, incomes=[], expenses=[], have=[])
#     actual = AccountsServiceNew(data).total

#     expect = {'past': 0.0, 'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'have': 0.0, 'delta': 0.0}

#     assert actual == expect


# def test_total_row_only_have(have):
#     data = SimpleNamespace(year=2000, incomes=[], expenses=[], have=have)
#     actual = AccountsServiceNew(data).total

#     expect = {'past': 0.0, 'incomes': 0.0, 'expenses': 0.0, 'balance': 0.0, 'have': 30.0, 'delta': 30.0}

#     assert actual == expect
