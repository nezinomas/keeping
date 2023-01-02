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


@pytest.fixture(name='types')
def fixture_types():
    return [
        SimpleNamespace(pk=1, closed=None),
        SimpleNamespace(pk=2, closed=None),
    ]


@pytest.mark.freeze_time('2000-12-31')
def test_table(incomes, expenses, have, types):
    incomes.extend([
        {'year': 1997, 'incomes': Decimal('5'), 'id': 1},
        {'year': 1998, 'incomes': Decimal('15'), 'id': 1},
    ])
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have, types=types)
    actual = Accounts(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1997
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 5.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 5.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == -5.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 1998
    assert actual[1]['past'] == 5.0
    assert actual[1]['incomes'] == 15.0
    assert actual[1]['expenses'] == 0.0
    assert actual[1]['balance'] == 20.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -20.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 1999
    assert actual[2]['past'] == 20.0
    assert actual[2]['incomes'] == 100.0
    assert actual[2]['expenses'] == 50.0
    assert actual[2]['balance'] == 70.0
    assert actual[2]['have'] == 10.0
    assert actual[2]['delta'] == -60.0
    assert actual[2]['latest_check'] == datetime(1999, 1, 1)

    assert actual[3]['id'] == 1
    assert actual[3]['year'] == 2000
    assert actual[3]['past'] == 70.0
    assert actual[3]['incomes'] == 200.0
    assert actual[3]['expenses'] == 100.0
    assert actual[3]['balance'] == 170.0
    assert actual[3]['have'] == 15.0
    assert actual[3]['delta'] == -155.0
    assert actual[3]['latest_check'] == datetime(2000, 1, 1)

    # future year=2001
    assert actual[4]['id'] == 1
    assert actual[4]['year'] == 2001
    assert actual[4]['past'] == 170.0
    assert actual[4]['incomes'] == 0.0
    assert actual[4]['expenses'] == 0.0
    assert actual[4]['balance'] == 170.0
    assert actual[4]['have'] == 15.0
    assert actual[4]['delta'] == -155.0
    assert actual[4]['latest_check'] == datetime(2000, 1, 1)

    # second account
    assert actual[5]['id'] == 2
    assert actual[5]['year'] == 1999
    assert actual[5]['past'] == 0.0
    assert actual[5]['incomes'] == 110.0
    assert actual[5]['expenses'] == 0.0
    assert actual[5]['balance'] == 110.0
    assert actual[5]['have'] == 20.0
    assert actual[5]['delta'] == -90.0
    assert actual[5]['latest_check'] == datetime(1999, 1, 1)

    assert actual[6]['id'] == 2
    assert actual[6]['year'] == 2000
    assert actual[6]['past'] == 110.0
    assert actual[6]['incomes'] == 220.0
    assert actual[6]['expenses'] == 110.0
    assert actual[6]['balance'] == 220.0
    assert actual[6]['have'] == 25.0
    assert actual[6]['delta'] == -195.0
    assert actual[6]['latest_check'] == datetime(2000, 1, 1)

    # future year=2001
    assert actual[7]['id'] == 2
    assert actual[7]['year'] == 2001
    assert actual[7]['past'] == 220.0
    assert actual[7]['incomes'] == 0.0
    assert actual[7]['expenses'] == 0.0
    assert actual[7]['balance'] == 220.0
    assert actual[7]['have'] == 25.0
    assert actual[7]['delta'] == -195.0
    assert actual[7]['latest_check'] == datetime(2000, 1, 1)


@pytest.mark.freeze_time('1999-1-1')
def test_table_with_types(incomes, types):
    incomes= [
        {'year': 1998, 'incomes': Decimal('1'), 'id': 1},
        {'year': 1998, 'incomes': Decimal('2'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('3'), 'id': 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1998
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 2.0

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['past'] == 2.0
    assert actual[4]['incomes'] == 0.0


@pytest.mark.freeze_time('1999-1-1')
def test_table_type_without_recods(incomes, types):
    types.append(SimpleNamespace(pk=666))
    incomes= [
        {'year': 1998, 'incomes': Decimal('1'), 'id': 1},
        {'year': 1998, 'incomes': Decimal('2'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('3'), 'id': 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1998
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 2.0

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['past'] == 2.0
    assert actual[4]['incomes'] == 0.0


@pytest.mark.freeze_time('1999-1-1')
def test_table_old_type(incomes, types):
    types.append(SimpleNamespace(pk=666))
    incomes= [
        {'year': 1974, 'incomes': Decimal('1'), 'id': 666},
        {'year': 1998, 'incomes': Decimal('1'), 'id': 1},
        {'year': 1998, 'incomes': Decimal('2'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('3'), 'id': 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1998
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 2.0

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['past'] == 2.0
    assert actual[4]['incomes'] == 0.0


@pytest.mark.freeze_time('2000-12-31')
def test_table_have_empty(incomes, expenses, types):
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=[], types=types)
    actual = Accounts(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 100.0
    assert actual[0]['expenses'] == 50.0
    assert actual[0]['balance'] == 50.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == -50.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past'] == 50.0
    assert actual[1]['incomes'] == 200.0
    assert actual[1]['expenses'] == 100.0
    assert actual[1]['balance'] == 150.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -150.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1999
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 110.0
    assert actual[3]['expenses'] == 0.0
    assert actual[3]['balance'] == 110.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -110.0
    assert actual[3]['latest_check'] == 0.0

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 2000
    assert actual[4]['past'] == 110.0
    assert actual[4]['incomes'] == 220.0
    assert actual[4]['expenses'] == 110.0
    assert actual[4]['balance'] == 220.0
    assert actual[4]['have'] == 0.0
    assert actual[4]['delta'] == -220.0
    assert actual[4]['latest_check'] == 0.0


@pytest.mark.freeze_time('2000-12-31')
def test_table_incomes_empty(expenses, types):
    data = SimpleNamespace(incomes=[], expenses=expenses, have=[], types=types)
    actual = Accounts(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 0.0
    assert actual[0]['expenses'] == 50.0
    assert actual[0]['balance'] == -50.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == 50.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past'] == -50.0
    assert actual[1]['incomes'] == 0.0
    assert actual[1]['expenses'] == 100.0
    assert actual[1]['balance'] == -150.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == 150.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past'] == -150.0
    assert actual[2]['incomes'] == 0.0
    assert actual[2]['expenses'] == 0.0
    assert actual[2]['balance'] == -150.0
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == 150.0
    assert actual[2]['latest_check'] == 0.0

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 2000
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 0.0
    assert actual[3]['expenses'] == 110.0
    assert actual[3]['balance'] == -110.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == 110.0
    assert actual[3]['latest_check'] == 0.0

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 2001
    assert actual[4]['past'] == -110.0
    assert actual[4]['incomes'] == 0.0
    assert actual[4]['expenses'] == 0.0
    assert actual[4]['balance'] == -110.0
    assert actual[4]['have'] == 0.0
    assert actual[4]['delta'] == 110.0
    assert actual[4]['latest_check'] == 0.0


@pytest.mark.freeze_time('2000-12-31')
def test_table_expenses_empty(incomes, types):
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Accounts(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 100.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 100.0
    assert actual[0]['have'] == 0.0
    assert actual[0]['delta'] == -100.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past'] == 100.0
    assert actual[1]['incomes'] == 200.0
    assert actual[1]['expenses'] == 0.0
    assert actual[1]['balance'] == 300.0
    assert actual[1]['have'] == 0.0
    assert actual[1]['delta'] == -300.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past'] == 300.0
    assert actual[2]['incomes'] == 0.0
    assert actual[2]['expenses'] == 0.0
    assert actual[2]['balance'] == 300.0
    assert actual[2]['have'] == 0.0
    assert actual[2]['delta'] == -300.0
    assert actual[2]['latest_check'] == 0.0

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1999
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 110.0
    assert actual[3]['expenses'] == 0.0
    assert actual[3]['balance'] == 110.0
    assert actual[3]['have'] == 0.0
    assert actual[3]['delta'] == -110.0
    assert actual[3]['latest_check'] == 0.0

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 2000
    assert actual[4]['past'] == 110.0
    assert actual[4]['incomes'] == 220.0
    assert actual[4]['expenses'] == 0.0
    assert actual[4]['balance'] == 330.0
    assert actual[4]['have'] == 0.0
    assert actual[4]['delta'] == -330.0
    assert actual[4]['latest_check'] == 0.0

    assert actual[5]['id'] == 2
    assert actual[5]['year'] == 2001
    assert actual[5]['past'] == 330.0
    assert actual[5]['incomes'] == 0.0
    assert actual[5]['expenses'] == 0.0
    assert actual[5]['balance'] == 330.0
    assert actual[5]['have'] == 0.0
    assert actual[5]['delta'] == -330.0
    assert actual[5]['latest_check'] == 0.0


def test_table_incomes_expenses_empty(types):
    data = SimpleNamespace(incomes=[], expenses=[], have=[], types=types)
    actual = Accounts(data).table

    expect = []

    assert actual == expect


@pytest.mark.freeze_time('2000-12-31')
def test_table_only_have(have, types):
    data = SimpleNamespace(incomes=[], expenses=[], have=have, types=types)
    actual = Accounts(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past'] == 0.0
    assert actual[0]['incomes'] == 0.0
    assert actual[0]['expenses'] == 0.0
    assert actual[0]['balance'] == 0.0
    assert actual[0]['have'] == 10.0
    assert actual[0]['delta'] == 10.0
    assert actual[0]['latest_check'] == datetime(1999, 1, 1)

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past'] == 0.0
    assert actual[1]['incomes'] == 0.0
    assert actual[1]['expenses'] == 0.0
    assert actual[1]['balance'] == 0.0
    assert actual[1]['have'] == 15.0
    assert actual[1]['delta'] == 15.0
    assert actual[1]['latest_check'] == datetime(2000, 1, 1)

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past'] == 0.0
    assert actual[2]['incomes'] == 0.0
    assert actual[2]['expenses'] == 0.0
    assert actual[2]['balance'] == 0.0
    assert actual[2]['have'] == 15.0
    assert actual[2]['delta'] == 15.0
    assert actual[2]['latest_check'] == datetime(2000, 1, 1)

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1999
    assert actual[3]['past'] == 0.0
    assert actual[3]['incomes'] == 0.0
    assert actual[3]['expenses'] == 0.0
    assert actual[3]['balance'] == 0.0
    assert actual[3]['have'] == 20.0
    assert actual[3]['delta'] == 20.0
    assert actual[3]['latest_check'] == datetime(1999, 1, 1)

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 2000
    assert actual[4]['past'] == 0.0
    assert actual[4]['incomes'] == 0.0
    assert actual[4]['expenses'] == 0.0
    assert actual[4]['balance'] == 0.0
    assert actual[4]['have'] == 25.0
    assert actual[4]['delta'] == 25.0
    assert actual[4]['latest_check'] == datetime(2000, 1, 1)

    assert actual[5]['id'] == 2
    assert actual[5]['year'] == 2001
    assert actual[5]['past'] == 0.0
    assert actual[5]['incomes'] == 0.0
    assert actual[5]['expenses'] == 0.0
    assert actual[5]['balance'] == 0.0
    assert actual[5]['have'] == 25.0
    assert actual[5]['delta'] == 25.0
    assert actual[5]['latest_check'] == datetime(2000, 1, 1)


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
