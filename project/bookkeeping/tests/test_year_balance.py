from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest
import time_machine

from ..lib.year_balance import YearBalance


@pytest.fixture(name="data")
def fixture_data():
    arr = [
        {
            "date": date(1999, 1, 1),
            "incomes": 55,
            "expenses": 15,
            "savings": 1,
            "savings_close": 5,
            "borrow": 25,
            "borrow_return": 15,
            "lend": 10,
            "lend_return": 5,
        },
        {
            "date": date(1999, 2, 1),
            "incomes": 125,
            "expenses": 0,
            "savings": 0,
            "savings_close": 0,
            "borrow": 0,
            "borrow_return": 0,
            "lend": 0,
            "lend_return": 0,
        },
    ]

    arr.extend(
        {
            "date": date(1999, i, 1),
            "incomes": 0,
            "expenses": 0,
            "savings": 0,
            "savings_close": 0,
            "borrow": 0,
            "borrow_return": 0,
            "lend": 0,
            "lend_return": 0,
        }
        for i in range(3, 13)
    )
    return SimpleNamespace(year=1999, data=pl.DataFrame(arr))


@pytest.fixture(name="amount_start")
def fixture_amount_start():
    return 1


@pytest.fixture(name="expect")
def fixture_expect():
    val = [
        {
            "date": date(1999, 1, 1),
            "incomes": 55,
            "expenses": 15,
            "balance": 40,
            "savings": 1,
            "savings_close": 5,
            "borrow": 25,
            "borrow_return": 15,
            "lend": 10,
            "lend_return": 5,
            "money_flow": 50,
        },
        {
            "date": date(1999, 2, 1),
            "incomes": 125,
            "expenses": 0,
            "balance": 125,
            "savings": 0,
            "savings_close": 0,
            "borrow": 0,
            "borrow_return": 0,
            "lend": 0,
            "lend_return": 0,
            "money_flow": 175,
        },
    ]

    # same dictionaries for march - december
    for i in range(3, 13):
        item = {
            "date": date(1999, i, 1),
            "incomes": 0,
            "expenses": 0,
            "balance": 0,
            "savings": 0,
            "savings_close": 0,
            "borrow": 0,
            "borrow_return": 0,
            "lend": 0,
            "lend_return": 0,
            "money_flow": 175,
        }
        val.append(item)

    return val


def test_months_balance(data, amount_start, expect):
    actual = YearBalance(data=data, amount_start=amount_start).balance
    assert actual == expect


def test_months_balance_total_row(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).total_row

    expect = {
        "incomes": 180,
        "expenses": 15,
        "balance": 165,
        "savings": 1,
        "savings_close": 5,
        "borrow": 25,
        "borrow_return": 15,
        "lend": 10,
        "lend_return": 5,
        "money_flow": 1975,
    }

    assert actual == expect


def test_months_balance_average(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).average

    expect = {
        "incomes": 90,
        "expenses": 15,
        "balance": 82.5,
        "savings": 1,
        "savings_close": 5,
        "borrow": 25,
        "borrow_return": 15,
        "lend": 10,
        "lend_return": 5,
        "money_flow": 164.58,
    }

    assert expect == pytest.approx(actual, rel=1e-2)


def test_amount_start(data):
    actual = YearBalance(data=data, amount_start=10).amount_start

    assert actual == 10


def test_amount_start_none(data):
    actual = YearBalance(data=data, amount_start=None).amount_start

    assert actual == 0


def test_amount_end(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).amount_end

    assert actual == 175


def test_amount_balance(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start).amount_balance

    assert actual == 165


def test_balance_income_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).income_data

    expect = [x["incomes"] for x in expect]

    assert actual == expect


def test_balance_expense_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).expense_data

    expect = [x["expenses"] for x in expect]

    assert actual == expect


def test_balance_borrow_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).borrow_data

    expect = [x["borrow"] for x in expect]

    assert actual == expect


def test_balance_borrow_return_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).borrow_return_data

    expect = [x["borrow_return"] for x in expect]

    assert actual == expect


def test_balance_lend_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).lend_data

    expect = [x["lend"] for x in expect]

    assert actual == expect


def test_balance_lend_return_data(data, expect):
    actual = YearBalance(data=data, amount_start=None).lend_return_data

    expect = [x["lend_return"] for x in expect]

    assert actual == expect


def test_balance_money_flow(data, amount_start, expect):
    actual = YearBalance(data=data, amount_start=amount_start).money_flow

    expect = [x["money_flow"] for x in expect]

    assert actual == expect


def test_avg_incomes(data):
    actual = YearBalance(data=data, amount_start=None).avg_incomes

    assert actual == 90


def test_avg_incomes_none(data):
    data.data = data.data.with_columns(pl.col("incomes") * 0)

    actual = YearBalance(data=data, amount_start=None).avg_incomes

    assert actual == 0


def test_avg_expenses(data):
    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 15


def test_avg_expenses_none(data):
    data.data = data.data.with_columns(pl.col("expenses") * 0)
    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 0


@time_machine.travel("1999-2-1")
def test_avg_expenses_current_year(data):
    data.data[0, "expenses"] = 1
    data.data[1, "expenses"] = 2
    data.data[2, "expenses"] = 3

    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 1.5


@time_machine.travel("2000-2-1")
def test_avg_expenses_not_current_year(data):
    data.data[0, "expenses"] = 1
    data.data[1, "expenses"] = 2
    data.data[2, "expenses"] = 3

    actual = YearBalance(data=data, amount_start=None).avg_expenses

    assert actual == 2
