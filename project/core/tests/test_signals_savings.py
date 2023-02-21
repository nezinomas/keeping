from datetime import datetime
from types import SimpleNamespace

import pytest
import time_machine

from ..lib.signals import Savings


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        # id: 1, year: 2000
        {'year': 2000, 'incomes': 100, 'fee': 2, 'id': 1},
        {'year': 2000, 'incomes': 100, 'fee': 2, 'id': 1},
        # id: 1, year: 1999
        {'year': 1999, 'incomes': 50, 'fee': 1, 'id': 1},
        {'year': 1999, 'incomes': 50, 'fee': 1, 'id': 1},
        # id: 2, year: 1999
        {'year': 1999, 'incomes': 55, 'fee': 3, 'id': 2},
        {'year': 1999, 'incomes': 55, 'fee': 3, 'id': 2},
        # id: 2, year: 2000
        {'year': 2000, 'incomes': 110, 'fee': 4, 'id': 2},
        {'year': 2000, 'incomes': 110, 'fee': 4, 'id': 2},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        # id: 1, year: 2000
        {'year': 2000, 'expenses': 50, 'fee': 2, 'id': 1},
        {'year': 2000, 'expenses': 50, 'fee': 2, 'id': 1},
        # id: 1, year: 1999
        {'year': 1999, 'expenses': 25, 'fee': 3, 'id': 1},
        {'year': 1999, 'expenses': 25, 'fee': 3, 'id': 1},
        # id: 2, year: 2000
        {'year': 2000, 'expenses': 55, 'fee': 1, 'id': 2},
        {'year': 2000, 'expenses': 55, 'fee': 1, 'id': 2},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {'id': 1, 'year': 1999, 'have': 75, 'latest_check': datetime(1999, 1, 1)},
        {'id': 1, 'year': 2000, 'have': 300, 'latest_check': datetime(2000, 1, 2)},
        {'id': 2, 'year': 1999, 'have': 100, 'latest_check': datetime(1999, 1, 3)},
        {'id': 2, 'year': 2000, 'have': 250, 'latest_check': datetime(2000, 1, 4)},
    ]


@pytest.fixture(name='types')
def fixture_types():
    return [
        SimpleNamespace(pk=1, closed=None),
        SimpleNamespace(pk=2, closed=None),
    ]


@time_machine.travel('2000-12-31')
def test_table(incomes, expenses, have, types):
    incomes.extend([
        {'year': 1998, 'incomes': 15, 'fee': 1, 'id': 1},
        {'year': 1997, 'incomes': 5, 'fee': 1, 'id': 1},
    ])
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have, types=types)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1997
    assert actual[0]['past_amount'] == 0
    assert actual[0]['past_fee'] == 0
    assert actual[0]['fee'] == 1
    assert actual[0]['per_year_incomes'] == 5
    assert actual[0]['per_year_fee'] == 1
    assert actual[0]['sold'] == 0
    assert actual[0]['sold_fee'] == 0
    assert actual[0]['incomes'] == 5
    assert actual[0]['invested'] == 4
    assert actual[0]['market_value'] == 0
    assert round(actual[0]['profit_proc'], 2) == -100
    assert actual[0]['profit_sum'] == -4
    assert not actual[0]['latest_check']

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 1998
    assert actual[1]['past_amount'] == 5
    assert actual[1]['past_fee'] == 1
    assert actual[1]['fee'] == 2
    assert actual[1]['per_year_incomes'] == 15
    assert actual[1]['per_year_fee'] == 1
    assert actual[1]['sold'] == 0
    assert actual[1]['sold_fee'] == 0
    assert actual[1]['incomes'] == 20
    assert actual[1]['invested'] == 18
    assert actual[1]['market_value'] == 0
    assert round(actual[1]['profit_proc'], 2) == -100
    assert actual[1]['profit_sum'] == -18
    assert not actual[1]['latest_check']

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 1999
    assert actual[2]['past_amount'] == 20
    assert actual[2]['past_fee'] == 2
    assert actual[2]['fee'] == 4
    assert actual[2]['per_year_incomes'] == 100
    assert actual[2]['per_year_fee'] == 2
    assert actual[2]['sold'] == 50
    assert actual[2]['sold_fee'] == 6
    assert actual[2]['incomes'] == 120
    assert actual[2]['invested'] == 60
    assert actual[2]['market_value'] == 75
    assert round(actual[2]['profit_proc'], 2) == 25
    assert actual[2]['profit_sum'] == 15
    assert actual[2]['latest_check'] == datetime(1999, 1, 1)

    assert actual[3]['id'] == 1
    assert actual[3]['year'] == 2000
    assert actual[3]['past_amount'] == 120
    assert actual[3]['past_fee'] == 4
    assert actual[3]['fee'] == 8
    assert actual[3]['per_year_incomes'] == 200
    assert actual[3]['per_year_fee'] == 4
    assert actual[3]['sold'] == 150
    assert actual[3]['sold_fee'] == 10
    assert actual[3]['incomes'] == 320
    assert actual[3]['invested'] == 152
    assert actual[3]['market_value'] == 300
    assert round(actual[3]['profit_proc'], 2) == 97.37
    assert actual[3]['profit_sum'] == 148
    assert actual[3]['latest_check'] == datetime(2000, 1, 2)

    assert actual[4]['id'] == 1
    assert actual[4]['year'] == 2001
    assert actual[4]['past_amount'] == 320
    assert actual[4]['past_fee'] == 8
    assert actual[4]['fee'] == 8
    assert actual[4]['per_year_incomes'] == 0
    assert actual[4]['per_year_fee'] == 0
    assert actual[4]['sold'] == 150
    assert actual[4]['sold_fee'] == 10
    assert actual[4]['incomes'] == 320
    assert actual[4]['invested'] == 152
    assert actual[4]['market_value'] == 300
    assert round(actual[4]['profit_proc'], 2) == 97.37
    assert actual[4]['profit_sum'] == 148
    assert actual[4]['latest_check'] == datetime(2000, 1, 2)

    assert actual[5]['id'] == 2
    assert actual[5]['year'] == 1999
    assert actual[5]['past_amount'] == 0
    assert actual[5]['past_fee'] == 0
    assert actual[5]['fee'] == 6
    assert actual[5]['per_year_incomes'] == 110
    assert actual[5]['per_year_fee'] == 6
    assert actual[5]['sold'] == 0
    assert actual[5]['sold_fee'] == 0
    assert actual[5]['incomes'] == 110
    assert actual[5]['invested'] == 104
    assert actual[5]['market_value'] == 100
    assert round(actual[5]['profit_proc'], 2) == -3.85
    assert actual[5]['profit_sum'] == -4
    assert actual[5]['latest_check'] == datetime(1999, 1, 3)

    assert actual[6]['id'] == 2
    assert actual[6]['year'] == 2000
    assert actual[6]['past_amount'] == 110
    assert actual[6]['past_fee'] == 6
    assert actual[6]['fee'] == 14
    assert actual[6]['per_year_incomes'] == 220
    assert actual[6]['per_year_fee'] == 8
    assert actual[6]['sold'] == 110
    assert actual[6]['sold_fee'] == 2
    assert actual[6]['incomes'] == 330
    assert actual[6]['invested'] == 204
    assert actual[6]['market_value'] == 250
    assert round(actual[6]['profit_proc'], 2) == 22.55
    assert actual[6]['profit_sum'] == 46
    assert actual[6]['latest_check'] == datetime(2000, 1, 4)

    assert actual[7]['id'] == 2
    assert actual[7]['year'] == 2001
    assert actual[7]['past_amount'] == 330
    assert actual[7]['past_fee'] == 14
    assert actual[7]['fee'] == 14
    assert actual[7]['per_year_incomes'] == 0
    assert actual[7]['per_year_fee'] == 0
    assert actual[7]['sold'] == 110
    assert actual[7]['sold_fee'] == 2
    assert actual[7]['incomes'] == 330
    assert actual[7]['invested'] == 204
    assert actual[7]['market_value'] == 250
    assert round(actual[7]['profit_proc'], 2) == 22.55
    assert actual[7]['profit_sum'] == 46
    assert actual[7]['latest_check'] == datetime(2000, 1, 4)


@time_machine.travel('1999-1-1')
def test_copy_market_value_and_latest_from_previous_year(types):
    have = [{'id': 1, 'year': 1998, 'have': 33, 'latest_check': datetime(1998, 1, 1)},]
    incomes = [
        {'year': 1998, 'incomes': 10, 'fee': 1, 'id': 1},
        {'year': 1999, 'incomes': 20, 'fee': 2, 'id': 1},
        {'year': 1998, 'incomes': 50, 'fee': 5, 'id': 2},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=have, types=types)
    actual = Savings(data).table

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 1999
    assert actual[1]['past_amount'] == 10
    assert actual[1]['past_fee'] == 1
    assert actual[1]['fee'] == 3
    assert actual[1]['per_year_incomes'] == 20
    assert actual[1]['per_year_fee'] == 2
    assert actual[1]['sold'] == 0
    assert actual[1]['sold_fee'] == 0
    assert actual[1]['incomes'] == 30
    assert actual[1]['invested'] == 27
    assert actual[1]['market_value'] == 33
    assert round(actual[1]['profit_proc'], 2) == 22.22
    assert actual[1]['profit_sum'] == 6
    assert actual[1]['latest_check'] == datetime(1998, 1, 1)


@time_machine.travel('1999-1-1')
def test_table_with_types(types):
    incomes = [
        {'year': 1998, 'incomes': 10, 'fee': 1, 'id': 1},
        {'year': 1998, 'incomes': 20, 'fee': 2, 'id': 2},
        {'year': 1999, 'incomes': 30, 'fee': 3, 'id': 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1998
    assert actual[0]['incomes'] == 10
    assert actual[0]['fee'] == 1
    assert actual[0]['past_amount'] == 0
    assert actual[0]['past_fee'] == 0
    assert actual[0]['per_year_incomes'] == 10
    assert actual[0]['per_year_fee'] == 1

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 1999
    assert actual[1]['incomes'] == 40
    assert actual[1]['fee'] == 4
    assert actual[1]['past_amount'] == 10
    assert actual[1]['past_fee'] == 1
    assert actual[1]['per_year_incomes'] == 30
    assert actual[1]['per_year_fee'] == 3

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2000
    assert actual[2]['incomes'] == 40
    assert actual[2]['fee'] == 4
    assert actual[2]['past_amount'] == 40
    assert actual[2]['past_fee'] == 4
    assert actual[2]['per_year_incomes'] == 0
    assert actual[2]['per_year_fee'] == 0

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1998
    assert actual[3]['incomes'] == 20
    assert actual[3]['fee'] == 2
    assert actual[3]['past_amount'] == 0
    assert actual[3]['past_fee'] == 0
    assert actual[3]['per_year_incomes'] == 20
    assert actual[3]['per_year_fee'] == 2

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['incomes'] == 20
    assert actual[4]['fee'] == 2
    assert actual[4]['past_amount'] == 20
    assert actual[4]['past_fee'] == 2
    assert actual[4]['per_year_incomes'] == 0
    assert actual[4]['per_year_fee'] == 0


@time_machine.travel('1999-1-1')
def test_table_type_without_record(types):
    types.append(SimpleNamespace(pk=666))
    incomes = [
        {'year': 1998, 'incomes': 10, 'fee': 1, 'id': 1},
        {'year': 1998, 'incomes': 20, 'fee': 2, 'id': 2},
        {'year': 1999, 'incomes': 30, 'fee': 3, 'id': 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Savings(data).table

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1998
    assert actual[3]['incomes'] == 20
    assert actual[3]['fee'] == 2
    assert actual[3]['past_amount'] == 0
    assert actual[3]['past_fee'] == 0
    assert actual[3]['per_year_incomes'] == 20
    assert actual[3]['per_year_fee'] == 2

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['incomes'] == 20
    assert actual[4]['fee'] == 2
    assert actual[4]['past_amount'] == 20
    assert actual[4]['past_fee'] == 2
    assert actual[4]['per_year_incomes'] == 0
    assert actual[4]['per_year_fee'] == 0


@time_machine.travel('1999-1-1')
def test_table_old_type(types):
    types.append(SimpleNamespace(pk=666))
    incomes = [
        {'year': 1974, 'incomes': 10, 'fee': 1, 'id': 666},
        {'year': 1998, 'incomes': 10, 'fee': 1, 'id': 1},
        {'year': 1998, 'incomes': 20, 'fee': 2, 'id': 2},
        {'year': 1999, 'incomes': 30, 'fee': 3, 'id': 1},
    ]
    data = SimpleNamespace(incomes=incomes, expenses=[], have=[], types=types)
    actual = Savings(data).table

    assert actual[3]['id'] == 2
    assert actual[3]['year'] == 1998
    assert actual[3]['incomes'] == 20
    assert actual[3]['fee'] == 2
    assert actual[3]['past_amount'] == 0
    assert actual[3]['past_fee'] == 0
    assert actual[3]['per_year_incomes'] == 20
    assert actual[3]['per_year_fee'] == 2

    assert actual[4]['id'] == 2
    assert actual[4]['year'] == 1999
    assert actual[4]['incomes'] == 20
    assert actual[4]['fee'] == 2
    assert actual[4]['past_amount'] == 20
    assert actual[4]['past_fee'] == 2
    assert actual[4]['per_year_incomes'] == 0
    assert actual[4]['per_year_fee'] == 0


@time_machine.travel('2000-12-31')
def test_table_have_empty(incomes, expenses, types):
    data = SimpleNamespace(incomes=incomes[:4], expenses=expenses[:4], have=[], types=types)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0
    assert actual[0]['past_fee'] == 0
    assert actual[0]['fee'] == 2
    assert actual[0]['per_year_incomes'] == 100
    assert actual[0]['per_year_fee'] == 2
    assert actual[0]['sold'] == 50
    assert actual[0]['sold_fee'] == 6
    assert actual[0]['incomes'] == 100
    assert actual[0]['invested'] == 42
    assert actual[0]['market_value'] == 0
    assert round(actual[0]['profit_proc'], 2) == -100
    assert actual[0]['profit_sum'] == -42
    assert not actual[0]['latest_check']

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 100
    assert actual[1]['past_fee'] == 2
    assert actual[1]['fee'] == 6
    assert actual[1]['per_year_incomes'] == 200
    assert actual[1]['per_year_fee'] == 4
    assert actual[1]['sold'] == 150
    assert actual[1]['sold_fee'] == 10
    assert actual[1]['incomes'] == 300
    assert actual[1]['invested'] == 134
    assert actual[1]['market_value'] == 0
    assert round(actual[1]['profit_proc'], 2) == -100
    assert actual[1]['profit_sum'] == -134
    assert not actual[1]['latest_check']

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 300
    assert actual[2]['past_fee'] == 6
    assert actual[2]['fee'] == 6
    assert actual[2]['per_year_incomes'] == 0
    assert actual[2]['per_year_fee'] == 0
    assert actual[2]['sold'] == 150
    assert actual[2]['sold_fee'] == 10
    assert actual[2]['incomes'] == 300
    assert actual[2]['invested'] == 134
    assert actual[2]['market_value'] == 0
    assert round(actual[2]['profit_proc'], 2) == -100
    assert actual[2]['profit_sum'] == -134
    assert not actual[2]['latest_check']


@time_machine.travel('2000-12-31')
def test_table_incomes_empty(expenses, types):
    data = SimpleNamespace(incomes=[], expenses=expenses[:4], have=[], types=types)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0
    assert actual[0]['past_fee'] == 0
    assert actual[0]['fee'] == 0
    assert actual[0]['per_year_incomes'] == 0
    assert actual[0]['per_year_fee'] == 0
    assert actual[0]['sold'] == 50
    assert actual[0]['sold_fee'] == 6
    assert actual[0]['incomes'] == 0
    assert actual[0]['invested'] == 0
    assert actual[0]['market_value'] == 0
    assert round(actual[0]['profit_proc'], 2) == 0
    assert actual[0]['profit_sum'] == 0
    assert not actual[0]['latest_check']

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 0
    assert actual[1]['past_fee'] == 0
    assert actual[1]['fee'] == 0
    assert actual[1]['per_year_incomes'] == 0
    assert actual[1]['per_year_fee'] == 0
    assert actual[1]['sold'] == 150
    assert actual[1]['sold_fee'] == 10
    assert actual[1]['incomes'] == 0
    assert actual[1]['invested'] == 0
    assert actual[1]['market_value'] == 0
    assert round(actual[1]['profit_proc'], 2) == 0
    assert actual[1]['profit_sum'] == 0
    assert not actual[1]['latest_check']

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 0
    assert actual[2]['past_fee'] == 0
    assert actual[2]['fee'] == 0
    assert actual[2]['per_year_incomes'] == 0
    assert actual[2]['per_year_fee'] == 0
    assert actual[2]['sold'] == 150
    assert actual[2]['sold_fee'] == 10
    assert actual[2]['incomes'] == 0
    assert actual[2]['invested'] == 0
    assert actual[2]['market_value'] == 0
    assert round(actual[2]['profit_proc'], 2) == 0
    assert actual[2]['profit_sum'] == 0
    assert not actual[2]['latest_check']


@time_machine.travel('2000-12-31')
def test_table_expenses_empty(incomes, types):
    data = SimpleNamespace(incomes=incomes[:4], expenses=[], have=[], types=types)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0
    assert actual[0]['past_fee'] == 0
    assert actual[0]['fee'] == 2
    assert actual[0]['per_year_incomes'] == 100
    assert actual[0]['per_year_fee'] == 2
    assert actual[0]['sold'] == 0
    assert actual[0]['sold_fee'] == 0
    assert actual[0]['incomes'] == 100
    assert actual[0]['invested'] == 98
    assert actual[0]['market_value'] == 0
    assert round(actual[0]['profit_proc'], 2) == -100
    assert actual[0]['profit_sum'] == -98
    assert not actual[0]['latest_check']

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 100
    assert actual[1]['past_fee'] == 2
    assert actual[1]['fee'] == 6
    assert actual[1]['per_year_incomes'] == 200
    assert actual[1]['per_year_fee'] == 4
    assert actual[1]['sold'] == 0
    assert actual[1]['sold_fee'] == 0
    assert actual[1]['incomes'] == 300
    assert actual[1]['invested'] == 294
    assert actual[1]['market_value'] == 0
    assert round(actual[1]['profit_proc'], 2) == -100
    assert actual[1]['profit_sum'] == -294
    assert not actual[1]['latest_check']

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 300
    assert actual[2]['past_fee'] == 6
    assert actual[2]['fee'] == 6
    assert actual[2]['per_year_incomes'] == 0
    assert actual[2]['per_year_fee'] == 0
    assert actual[2]['sold'] == 0
    assert actual[2]['sold_fee'] == 0
    assert actual[2]['incomes'] == 300
    assert actual[2]['invested'] == 294
    assert actual[2]['market_value'] == 0
    assert round(actual[2]['profit_proc'], 2) == -100
    assert actual[2]['profit_sum'] == -294
    assert not actual[2]['latest_check']


@time_machine.travel('2000-12-31')
def test_table_only_have(have, types):
    data = SimpleNamespace(incomes=[], expenses=[], have=have[:2], types=types)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0
    assert actual[0]['past_fee'] == 0
    assert actual[0]['fee'] == 0
    assert actual[0]['per_year_incomes'] == 0
    assert actual[0]['per_year_fee'] == 0
    assert actual[0]['sold'] == 0
    assert actual[0]['sold_fee'] == 0
    assert actual[0]['incomes'] == 0
    assert actual[0]['invested'] == 0
    assert actual[0]['market_value'] == 75
    assert round(actual[0]['profit_proc'], 2) == 0
    assert actual[0]['profit_sum'] == 75
    assert actual[0]['latest_check'] == datetime(1999, 1, 1)

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 0
    assert actual[1]['past_fee'] == 0
    assert actual[1]['fee'] == 0
    assert actual[1]['per_year_incomes'] == 0
    assert actual[1]['per_year_fee'] == 0
    assert actual[1]['sold'] == 0
    assert actual[1]['sold_fee'] == 0
    assert actual[1]['incomes'] == 0
    assert actual[1]['invested'] == 0
    assert actual[1]['market_value'] == 300
    assert round(actual[1]['profit_proc'], 2) == 0
    assert actual[1]['profit_sum'] == 300
    assert actual[1]['latest_check'] == datetime(2000, 1, 2)

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 0
    assert actual[2]['past_fee'] == 0
    assert actual[2]['fee'] == 0
    assert actual[2]['per_year_incomes'] == 0
    assert actual[2]['per_year_fee'] == 0
    assert actual[2]['sold'] == 0
    assert actual[2]['sold_fee'] == 0
    assert actual[2]['incomes'] == 0
    assert actual[2]['invested'] == 0
    assert actual[2]['market_value'] == 300
    assert round(actual[2]['profit_proc'], 2) == 0
    assert actual[2]['profit_sum'] == 300
    assert actual[2]['latest_check'] == datetime(2000, 1, 2)
