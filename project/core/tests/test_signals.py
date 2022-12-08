from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ..signals import Accounts, create_objects


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
        {'id': 1, 'year': 1999, 'have': Decimal('10'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 1, 'year': 2000, 'have': Decimal('15'), 'latest_check': datetime(2000, 1, 1)},
        {'id': 2, 'year': 1999, 'have': Decimal('20'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 2, 'year': 2000, 'have': Decimal('25'), 'latest_check': datetime(2000, 1, 1)},
    ]


def test_table(incomes, expenses, have):
    incomes.extend([
        {'year': 1997, 'incomes': Decimal('5'), 'id': 1},
        {'year': 1998, 'incomes': Decimal('15'), 'id': 1},
    ])
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have)
    actual = Accounts(data).table

    expect = [
        dict(
            id=1, year=1997, past=0.0, incomes=5.0, expenses=0.0, balance=5.0, have=0.0, delta=-5.0, latest_check=0.0),
        dict(
            id=1, year=1998, past=5.0, incomes=15.0, expenses=0.0, balance=20.0, have=0.0, delta=-20.0, latest_check=0.0),
        dict(
            id=1, year=1999, past=20.0, incomes=100.0, expenses=50.0, balance=70.0, have=10.0, delta=-60.0, latest_check=datetime(1999, 1, 1)),
        dict(
            id=1, year=2000, past=70.0, incomes=200.0, expenses=100.0, balance=170.0, have=15.0, delta=-155.0, latest_check=datetime(2000, 1, 1)),
        dict(
            id=2, year=1999, past=0.0, incomes=110.0, expenses=0.0, balance=110.0, have=20.0, delta=-90.0, latest_check=datetime(1999, 1, 1)),
        dict(
            id=2, year=2000, past=110.0, incomes=220.0, expenses=110.0, balance=220.0, have=25.0, delta=-195.0, latest_check=datetime(2000, 1, 1)),
    ]

    assert actual == expect


def test_table_have_empty(incomes, expenses):
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=[])
    actual = Accounts(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=100.0, expenses=50.0, balance=50.0, have=0.0, delta=-50.0, latest_check=0.0),
        dict(
            id=1, year=2000, past=50.0, incomes=200.0, expenses=100.0, balance=150.0, have=0.0, delta=-150.0, latest_check=0.0),
        dict(
            id=2, year=1999, past=0.0, incomes=110.0, expenses=0.0, balance=110.0, have=0.0, delta=-110.0, latest_check=0.0),
        dict(
            id=2, year=2000, past=110.0, incomes=220.0, expenses=110.0, balance=220.0, have=0.0, delta=-220.0, latest_check=0.0),
    ]

    assert actual == expect


def test_table_incomes_empty(expenses):
    data = SimpleNamespace(incomes=[], expenses=expenses, have=[])
    actual = Accounts(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=0.0, expenses=50.0, balance=-50.0, have=0.0, delta=50.0, latest_check=0.0),
        dict(
            id=1, year=2000, past=-50.0, incomes=0.0, expenses=100.0, balance=-150.0, have=0.0, delta=150.0, latest_check=0.0),
        dict(
            id=2, year=2000, past=0.0, incomes=0.0, expenses=110.0, balance=-110.0, have=0.0, delta=110.0, latest_check=0.0),
    ]

    assert actual == expect


def test_table_expenses_empty(incomes):
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[])
    actual = Accounts(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=100.0, expenses=0.0, balance=100.0, have=0.0, delta=-100.0, latest_check=0.0),
        dict(
            id=1, year=2000, past=100.0, incomes=200.0, expenses=0.0, balance=300.0, have=0.0, delta=-300.0, latest_check=0.0),
        dict(
            id=2, year=1999, past=0.0, incomes=110.0, expenses=0.0, balance=110.0, have=0.0, delta=-110.0, latest_check=0.0),
        dict(
            id=2, year=2000, past=110.0, incomes=220.0, expenses=0.0, balance=330.0, have=0.0, delta=-330.0, latest_check=0.0),
    ]

    assert actual == expect


def test_table_incomes_expenses_empty():
    data = SimpleNamespace(incomes=[], expenses=[], have=[])
    actual = Accounts(data).table

    expect = []

    assert actual == expect


def test_table_only_have(have):
    data = SimpleNamespace(incomes=[], expenses=[], have=have)
    actual = Accounts(data).table

    expect = [
        dict(
            id=1, year=1999, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=10.0, delta=10.0, latest_check=datetime(1999, 1, 1)),
        dict(
            id=1, year=2000, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=15.0, delta=15.0, latest_check=datetime(2000, 1, 1)),
        dict(
            id=2, year=1999, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=20.0, delta=20.0, latest_check=datetime(1999, 1, 1)),
        dict(
            id=2, year=2000, past=0.0, incomes=0.0, expenses=0.0, balance=0.0, have=25.0, delta=25.0, latest_check=datetime(2000, 1, 1)),
    ]

    assert actual == expect


def test_create_objects():
    account = AccountFactory.build()

    data = [
        dict(
            id=1, year=1999, past=1.0, incomes=2.0, expenses=3.0, balance=4.0, have=5.0, delta=6.0, latest_check=datetime(1999, 1, 1))
    ]
    actual = create_objects(AccountBalance, {1: account}, data)[0]

    assert actual.account == account
    assert actual.year == 1999
    assert actual.past == 1.0
    assert actual.incomes == 2.0
    assert actual.expenses == 3.0
    assert actual.balance == 4.0
    assert actual.have == 5.0
    assert actual.delta == 6.0
    assert actual.latest_check == datetime(1999, 1, 1)
