from datetime import datetime, date
from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
import pytest
from freezegun import freeze_time
from pandas import Timestamp as pdTime

from ..lib.year_balance import YearBalance


@pytest.fixture(name='data')
def fixture_data():
    arr = [
        {'date': date(1999, 1, 1), 'incomes': 5.5, 'expenses': 1.75, 'savings': 1.0, 'savings_close': 0.5, 'borrow': 0.25, 'borrow_return': 0.15, 'lend': 1, 'lend_return': 0.5},
        {'date': date(1999, 2, 1), 'incomes': 1.25, 'expenses': 0, 'savings': 0, 'savings_close': 0, 'borrow': 0, 'borrow_return': 0, 'lend': 0, 'lend_return': 0}
    ]

    for i in range(3, 13):
        arr.append(
            {'date': date(1999, i, 1), 'incomes': 0, 'expenses': 0, 'savings': 0, 'savings_close': 0, 'borrow': 0, 'borrow_return': 0, 'lend': 0, 'lend_return': 0}
        )

    df = pd.DataFrame(arr)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return SimpleNamespace(year=1999, data=df)


@pytest.fixture(name='amount_start')
def fixture_amount_start():
    return Decimal(1)


@pytest.fixture(name='expect')
def fixture_expect():
    val = [
        {
            'date': pdTime(date(1999, 1, 1)),
            'incomes': 5.5,
            'expenses': 1.75,
            'balance': 3.75,
            'savings': 1.0,
            'savings_close': 0.5,
            'borrow': 0.25,
            'borrow_return': 0.15,
            'lend': 1.0,
            'lend_return': 0.5,
            'money_flow': 3.85
        }, {
            'date': pdTime(date(1999, 2, 1)),
            'incomes': 1.25,
            'expenses': 0.0,
            'balance': 1.25,
            'savings': 0.0,
            'savings_close': 0.0,
            'borrow': 0.0,
            'borrow_return': 0.0,
            'lend': 0.0,
            'lend_return': 0.0,
            'money_flow': 5.1
        }
    ]

    # same dictionaries for march - december
    for i in range(3, 13):
        item = {
            'date': pdTime(date(1999, i, 1)),
            'incomes': 0.0,
            'expenses': 0.0,
            'balance': 0.0,
            'savings': 0.0,
            'savings_close': 0.0,
            'borrow': 0.0,
            'borrow_return': 0.0,
            'lend': 0.0,
            'lend_return': 0.0,
            'money_flow': 5.1
        }
        val.append(item)

    return val


def test_months_balance(data, amount_start, expect):
    actual = YearBalance(data=data, amount_start=amount_start).balance
    assert actual == expect


def test_months_balance_total_row(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).total_row

    expect = {
        'incomes': 6.75,
        'expenses': 1.75,
        'balance': 5.0,
        'savings': 1.0,
        'savings_close': 0.5,
        'borrow': 0.25,
        'borrow_return': 0.15,
        'lend': 1.0,
        'lend_return': 0.5,
        'money_flow': 59.95
    }

    assert actual == expect


def test_months_balance_average(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).average

    expect = {
        'incomes': 3.38,
        'expenses': 1.75,
        'balance': 2.5,
        'savings': 1.0,
        'savings_close': 0.5,
        'borrow': 0.25,
        'borrow_return': 0.15,
        'lend': 1.0,
        'lend_return': 0.5,
        'money_flow': 5.0
    }

    assert expect == pytest.approx(actual, rel=1e-2)


def test_amount_start(data):
    actual = YearBalance(data=data, amount_start=10).amount_start

    assert actual == 10


def test_amount_start_none(data):
    actual = YearBalance(data=data, amount_start=None).amount_start

    assert actual == 0.0


def test_amount_end(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).amount_end

    assert actual == 5.1


def test_amount_end_no_amount_start(data):
    actual = YearBalance(data=data)
    del actual._balance['money_flow']

    assert actual.amount_end == 0.0


def test_amount_end_none(data):
    data.data.loc[:,:] = 0
    actual = YearBalance(data=data, amount_start=None).amount_end

    assert actual == 0.0


def test_amount_balance(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).amount_balance

    assert actual == 5.0


def test_balance_income_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).income_data

    expect = [x['incomes'] for x in expect]

    assert actual == expect


def test_balance_expense_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).expense_data

    expect = [x['expenses'] for x in expect]

    assert actual == expect


def test_balance_borrow_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).borrow_data

    expect = [x['borrow'] for x in expect]

    assert actual == expect


def test_balance_borrow_return_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).borrow_return_data

    expect = [x['borrow_return'] for x in expect]

    assert actual == expect


def test_balance_lend_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).lend_data

    expect = [x['lend'] for x in expect]

    assert actual == expect


def test_balance_lend_return_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).lend_return_data

    expect = [x['lend_return'] for x in expect]

    assert actual == expect


def test_balance_money_flow(data, amount_start, expect):
    actual = YearBalance(data=data, amount_start=amount_start).money_flow

    expect = [x['money_flow'] for x in expect]

    assert actual == expect


def test_avg_incomes(data):
    actual = YearBalance(data=data, amount_start=None).avg_incomes

    assert pytest.approx(actual, rel=1e-2) == 3.38


def test_avg_incomes_none(data):
    data.data['incomes'] = 0
    actual = YearBalance(data=data, amount_start=None).avg_incomes

    assert actual == 0.0


def test_avg_expenses(data):
    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 1.75


def test_avg_expenses_none(data):
    data.data['expenses'] = 0
    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 0.0


@freeze_time('1999-2-1')
def test_avg_expenses_current_year(data):
    data.data.at[datetime(1999, 1, 1), 'expenses'] = 1
    data.data.at[datetime(1999, 2, 1), 'expenses'] = 2
    data.data.at[datetime(1999, 3, 1), 'expenses'] = 3

    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 1.5


@freeze_time('2000-2-1')
def test_avg_expenses_not_current_year(data):
    data.data.at[datetime(1999, 1, 1), 'expenses'] = 1
    data.data.at[datetime(1999, 2, 1), 'expenses'] = 2
    data.data.at[datetime(1999, 3, 1), 'expenses'] = 3

    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 2.0
