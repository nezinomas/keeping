from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from ..signals import Savings
import pytest


@pytest.fixture(name="incomes")
def fixture_incomes():
    return [
        # id: 1, year: 2000
        {'year': 2000, 'incomes': Decimal('100'), 'fee': Decimal('2'), 'id': 1},
        {'year': 2000, 'incomes': Decimal('100'), 'fee': Decimal('2'), 'id': 1},
        # id: 1, year: 1999
        {'year': 1999, 'incomes': Decimal('50'), 'fee': Decimal('1'), 'id': 1},
        {'year': 1999, 'incomes': Decimal('50'), 'fee': Decimal('1'), 'id': 1},
        # id: 2, year: 1999
        {'year': 1999, 'incomes': Decimal('55'), 'fee': Decimal('3'), 'id': 2},
        {'year': 1999, 'incomes': Decimal('55'), 'fee': Decimal('3'), 'id': 2},
        # id: 2, year: 2000
        {'year': 2000, 'incomes': Decimal('110'), 'fee': Decimal('4'), 'id': 2},
        {'year': 2000, 'incomes': Decimal('110'), 'fee': Decimal('4'), 'id': 2},
    ]


@pytest.fixture(name="expenses")
def fixture_expenses():
    return [
        # id: 1, year: 2000
        {'year': 2000, 'expenses': Decimal('50'), 'fee': Decimal('2'), 'id': 1},
        {'year': 2000, 'expenses': Decimal('50'), 'fee': Decimal('2'), 'id': 1},
        # id: 1, year: 1999
        {'year': 1999, 'expenses': Decimal('25'), 'fee': Decimal('3'), 'id': 1},
        {'year': 1999, 'expenses': Decimal('25'), 'fee': Decimal('3'), 'id': 1},
        # id: 2, year: 2000
        {'year': 2000, 'expenses': Decimal('55'), 'fee': Decimal('1'), 'id': 2},
        {'year': 2000, 'expenses': Decimal('55'), 'fee': Decimal('1'), 'id': 2},
    ]


@pytest.fixture(name="have")
def fixture_have():
    return [
        {'id': 1, 'year': 1999, 'have': Decimal('75'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 1, 'year': 2000, 'have': Decimal('300'), 'latest_check': datetime(2000, 1, 1)},
        {'id': 2, 'year': 1999, 'have': Decimal('100'), 'latest_check': datetime(1999, 1, 1)},
        {'id': 2, 'year': 2000, 'have': Decimal('250'), 'latest_check': datetime(2000, 1, 1)},
    ]


@pytest.mark.freeze_time('2000-12-31')
def test_table(incomes, expenses, have):
    incomes.extend([
        {'year': 1998, 'incomes': Decimal('15'), 'fee': Decimal('1'), 'id': 1},
        {'year': 1997, 'incomes': Decimal('5'), 'fee': Decimal('1'), 'id': 1},
    ])
    data = SimpleNamespace(incomes=incomes, expenses=expenses, have=have)
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1997
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fee'] == 1.0
    assert actual[0]['per_year_incomes'] == 5.0
    assert actual[0]['per_year_fee'] == 1.0
    assert actual[0]['sold'] == 0.0
    assert actual[0]['sold_fee'] == 0.0
    assert actual[0]['incomes'] == 5.0
    assert actual[0]['invested'] == 4.0
    assert actual[0]['market_value'] == 0.0
    assert round(actual[0]['profit_proc'], 2) == -100.0
    assert actual[0]['profit_sum'] == -4.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 1998
    assert actual[1]['past_amount'] == 5.0
    assert actual[1]['past_fee'] == 1.0
    assert actual[1]['fee'] == 2.0
    assert actual[1]['per_year_incomes'] == 15.0
    assert actual[1]['per_year_fee'] == 1.0
    assert actual[1]['sold'] == 0.0
    assert actual[1]['sold_fee'] == 0.0
    assert actual[1]['incomes'] == 20.0
    assert actual[1]['invested'] == 18.0
    assert actual[1]['market_value'] == 0.0
    assert round(actual[1]['profit_proc'], 2) == -100.0
    assert actual[1]['profit_sum'] == -18.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 1999
    assert actual[2]['past_amount'] == 20.0
    assert actual[2]['past_fee'] == 2.0
    assert actual[2]['fee'] == 4.0
    assert actual[2]['per_year_incomes'] == 100.0
    assert actual[2]['per_year_fee'] == 2.0
    assert actual[2]['sold'] == 50.0
    assert actual[2]['sold_fee'] == 6.0
    assert actual[2]['incomes'] == 120.0
    assert actual[2]['invested'] == 60.0
    assert actual[2]['market_value'] == 75.0
    assert round(actual[2]['profit_proc'], 2) == 25.0
    assert actual[2]['profit_sum'] == 15.0
    assert actual[2]['latest_check'] == datetime(1999, 1, 1)

    assert actual[3]['id'] == 1
    assert actual[3]['year'] == 2000
    assert actual[3]['past_amount'] == 120.0
    assert actual[3]['past_fee'] == 4.0
    assert actual[3]['fee'] == 8.0
    assert actual[3]['per_year_incomes'] == 200.0
    assert actual[3]['per_year_fee'] == 4.0
    assert actual[3]['sold'] == 150.0
    assert actual[3]['sold_fee'] == 10.0
    assert actual[3]['incomes'] == 320.0
    assert actual[3]['invested'] == 152.0
    assert actual[3]['market_value'] == 300.0
    assert round(actual[3]['profit_proc'], 2) == 97.37
    assert actual[3]['profit_sum'] == 148.0
    assert actual[3]['latest_check'] == datetime(2000, 1, 1)

    assert actual[4]['id'] == 1
    assert actual[4]['year'] == 2001
    assert actual[4]['past_amount'] == 320.0
    assert actual[4]['past_fee'] == 8.0
    assert actual[4]['fee'] == 8.0
    assert actual[4]['per_year_incomes'] == 0.0
    assert actual[4]['per_year_fee'] == 0.0
    assert actual[4]['sold'] == 150.0
    assert actual[4]['sold_fee'] == 10.0
    assert actual[4]['incomes'] == 320.0
    assert actual[4]['invested'] == 152.0
    assert actual[4]['market_value'] == 300.0
    assert round(actual[4]['profit_proc'], 2) == 97.37
    assert actual[4]['profit_sum'] == 148.0
    assert actual[4]['latest_check'] == datetime(2000, 1, 1)

    assert actual[5]['id'] == 2
    assert actual[5]['year'] == 1999
    assert actual[5]['past_amount'] == 0.0
    assert actual[5]['past_fee'] == 0.0
    assert actual[5]['fee'] == 6.0
    assert actual[5]['per_year_incomes'] == 110.0
    assert actual[5]['per_year_fee'] == 6.0
    assert actual[5]['sold'] == 0.0
    assert actual[5]['sold_fee'] == 0.0
    assert actual[5]['incomes'] == 110.0
    assert actual[5]['invested'] == 104.0
    assert actual[5]['market_value'] == 100.0
    assert round(actual[5]['profit_proc'], 2) == -3.85
    assert actual[5]['profit_sum'] == -4.0
    assert actual[5]['latest_check'] == datetime(1999, 1, 1)

    assert actual[6]['id'] == 2
    assert actual[6]['year'] == 2000
    assert actual[6]['past_amount'] == 110.0
    assert actual[6]['past_fee'] == 6.0
    assert actual[6]['fee'] == 14.0
    assert actual[6]['per_year_incomes'] == 220.0
    assert actual[6]['per_year_fee'] == 8.0
    assert actual[6]['sold'] == 110.0
    assert actual[6]['sold_fee'] == 2.0
    assert actual[6]['incomes'] == 330.0
    assert actual[6]['invested'] == 204.0
    assert actual[6]['market_value'] == 250.0
    assert round(actual[6]['profit_proc'], 2) == 22.55
    assert actual[6]['profit_sum'] == 46.0
    assert actual[6]['latest_check'] == datetime(2000, 1, 1)

    assert actual[7]['id'] == 2
    assert actual[7]['year'] == 2001
    assert actual[7]['past_amount'] == 330.0
    assert actual[7]['past_fee'] == 14.0
    assert actual[7]['fee'] == 14.0
    assert actual[7]['per_year_incomes'] == 0.0
    assert actual[7]['per_year_fee'] == 0.0
    assert actual[7]['sold'] == 110.0
    assert actual[7]['sold_fee'] == 2.0
    assert actual[7]['incomes'] == 330.0
    assert actual[7]['invested'] == 204.0
    assert actual[7]['market_value'] == 250.0
    assert round(actual[7]['profit_proc'], 2) == 22.55
    assert actual[7]['profit_sum'] == 46.0
    assert actual[7]['latest_check'] == datetime(2000, 1, 1)


@pytest.mark.freeze_time('2000-12-31')
def test_table_have_empty(incomes, expenses):
    data = SimpleNamespace(incomes=incomes[:4], expenses=expenses[:4], have=[])
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fee'] == 2.0
    assert actual[0]['per_year_incomes'] == 100.0
    assert actual[0]['per_year_fee'] == 2.0
    assert actual[0]['sold'] == 50.0
    assert actual[0]['sold_fee'] == 6.0
    assert actual[0]['incomes'] == 100.0
    assert actual[0]['invested'] == 42.0
    assert actual[0]['market_value'] == 0.0
    assert round(actual[0]['profit_proc'], 2) == -100.0
    assert actual[0]['profit_sum'] == -42.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 100.0
    assert actual[1]['past_fee'] == 2.0
    assert actual[1]['fee'] == 6.0
    assert actual[1]['per_year_incomes'] == 200.0
    assert actual[1]['per_year_fee'] == 4.0
    assert actual[1]['sold'] == 150.0
    assert actual[1]['sold_fee'] == 10.0
    assert actual[1]['incomes'] == 300.0
    assert actual[1]['invested'] == 134.0
    assert actual[1]['market_value'] == 0.0
    assert round(actual[1]['profit_proc'], 2) == -100.0
    assert actual[1]['profit_sum'] == -134.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 300.0
    assert actual[2]['past_fee'] == 6.0
    assert actual[2]['fee'] == 6.0
    assert actual[2]['per_year_incomes'] == 0.0
    assert actual[2]['per_year_fee'] == 0.0
    assert actual[2]['sold'] == 150.0
    assert actual[2]['sold_fee'] == 10.0
    assert actual[2]['incomes'] == 300.0
    assert actual[2]['invested'] == 134.0
    assert actual[2]['market_value'] == 0.0
    assert round(actual[2]['profit_proc'], 2) == -100.0
    assert actual[2]['profit_sum'] == -134.0
    assert actual[2]['latest_check'] == 0.0


@pytest.mark.freeze_time('2000-12-31')
def test_table_incomes_empty(expenses):
    data = SimpleNamespace(incomes=[], expenses=expenses[:4], have=[])
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fee'] == 0.0
    assert actual[0]['per_year_incomes'] == 0.0
    assert actual[0]['per_year_fee'] == 0.0
    assert actual[0]['sold'] == 50.0
    assert actual[0]['sold_fee'] == 6.0
    assert actual[0]['incomes'] == 0.0
    assert actual[0]['invested'] == 0.0
    assert actual[0]['market_value'] == 0.0
    assert round(actual[0]['profit_proc'], 2) == 0.0
    assert actual[0]['profit_sum'] == 0.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 0.0
    assert actual[1]['past_fee'] == 0.0
    assert actual[1]['fee'] == 0.0
    assert actual[1]['per_year_incomes'] == 0.0
    assert actual[1]['per_year_fee'] == 0.0
    assert actual[1]['sold'] == 150.0
    assert actual[1]['sold_fee'] == 10.0
    assert actual[1]['incomes'] == 0.0
    assert actual[1]['invested'] == 0.0
    assert actual[1]['market_value'] == 0.0
    assert round(actual[1]['profit_proc'], 2) == 0.0
    assert actual[1]['profit_sum'] == 0.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 0.0
    assert actual[2]['past_fee'] == 0.0
    assert actual[2]['fee'] == 0.0
    assert actual[2]['per_year_incomes'] == 0.0
    assert actual[2]['per_year_fee'] == 0.0
    assert actual[2]['sold'] == 150.0
    assert actual[2]['sold_fee'] == 10.0
    assert actual[2]['incomes'] == 0.0
    assert actual[2]['invested'] == 0.0
    assert actual[2]['market_value'] == 0.0
    assert round(actual[2]['profit_proc'], 2) == 0.0
    assert actual[2]['profit_sum'] == 0.0
    assert actual[2]['latest_check'] == 0.0


@pytest.mark.freeze_time('2000-12-31')
def test_table_expenses_empty(incomes):
    data = SimpleNamespace(incomes=incomes[:4], expenses=[], have=[])
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fee'] == 2.0
    assert actual[0]['per_year_incomes'] == 100.0
    assert actual[0]['per_year_fee'] == 2.0
    assert actual[0]['sold'] == 0.0
    assert actual[0]['sold_fee'] == 0.0
    assert actual[0]['incomes'] == 100.0
    assert actual[0]['invested'] == 98.0
    assert actual[0]['market_value'] == 0.0
    assert round(actual[0]['profit_proc'], 2) == -100.0
    assert actual[0]['profit_sum'] == -98.0
    assert actual[0]['latest_check'] == 0.0

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 100.0
    assert actual[1]['past_fee'] == 2.0
    assert actual[1]['fee'] == 6.0
    assert actual[1]['per_year_incomes'] == 200.0
    assert actual[1]['per_year_fee'] == 4.0
    assert actual[1]['sold'] == 0.0
    assert actual[1]['sold_fee'] == 0.0
    assert actual[1]['incomes'] == 300.0
    assert actual[1]['invested'] == 294.0
    assert actual[1]['market_value'] == 0.0
    assert round(actual[1]['profit_proc'], 2) == -100.0
    assert actual[1]['profit_sum'] == -294.0
    assert actual[1]['latest_check'] == 0.0

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 300.0
    assert actual[2]['past_fee'] == 6.0
    assert actual[2]['fee'] == 6.0
    assert actual[2]['per_year_incomes'] == 0.0
    assert actual[2]['per_year_fee'] == 0.0
    assert actual[2]['sold'] == 0.0
    assert actual[2]['sold_fee'] == 0.0
    assert actual[2]['incomes'] == 300.0
    assert actual[2]['invested'] == 294.0
    assert actual[2]['market_value'] == 0.0
    assert round(actual[2]['profit_proc'], 2) == -100.0
    assert actual[2]['profit_sum'] == -294.0
    assert actual[2]['latest_check'] == 0.0


@pytest.mark.freeze_time('2000-12-31')
def test_table_only_have(have):
    data = SimpleNamespace(incomes=[], expenses=[], have=have[:2])
    actual = Savings(data).table

    assert actual[0]['id'] == 1
    assert actual[0]['year'] == 1999
    assert actual[0]['past_amount'] == 0.0
    assert actual[0]['past_fee'] == 0.0
    assert actual[0]['fee'] == 0.0
    assert actual[0]['per_year_incomes'] == 0.0
    assert actual[0]['per_year_fee'] == 0.0
    assert actual[0]['sold'] == 0.0
    assert actual[0]['sold_fee'] == 0.0
    assert actual[0]['incomes'] == 0.0
    assert actual[0]['invested'] == 0.0
    assert actual[0]['market_value'] == 75.0
    assert round(actual[0]['profit_proc'], 2) == 0.0
    assert actual[0]['profit_sum'] == 75.0
    assert actual[0]['latest_check'] == datetime(1999, 1, 1)

    assert actual[1]['id'] == 1
    assert actual[1]['year'] == 2000
    assert actual[1]['past_amount'] == 0.0
    assert actual[1]['past_fee'] == 0.0
    assert actual[1]['fee'] == 0.0
    assert actual[1]['per_year_incomes'] == 0.0
    assert actual[1]['per_year_fee'] == 0.0
    assert actual[1]['sold'] == 0.0
    assert actual[1]['sold_fee'] == 0.0
    assert actual[1]['incomes'] == 0.0
    assert actual[1]['invested'] == 0.0
    assert actual[1]['market_value'] == 300.0
    assert round(actual[1]['profit_proc'], 2) == 0.0
    assert actual[1]['profit_sum'] == 300.0
    assert actual[1]['latest_check'] == datetime(2000, 1, 1)

    assert actual[2]['id'] == 1
    assert actual[2]['year'] == 2001
    assert actual[2]['past_amount'] == 0.0
    assert actual[2]['past_fee'] == 0.0
    assert actual[2]['fee'] == 0.0
    assert actual[2]['per_year_incomes'] == 0.0
    assert actual[2]['per_year_fee'] == 0.0
    assert actual[2]['sold'] == 0.0
    assert actual[2]['sold_fee'] == 0.0
    assert actual[2]['incomes'] == 0.0
    assert actual[2]['invested'] == 0.0
    assert actual[2]['market_value'] == 300.0
    assert round(actual[2]['profit_proc'], 2) == 0.0
    assert actual[2]['profit_sum'] == 300.0
    assert actual[2]['latest_check'] == datetime(2000, 1, 1)
