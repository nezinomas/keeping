from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest

from ...lib.make_dataframe import YearMonths
from ...lib.year_balance import YearBalance

TODAY = date(2000, 1, 1)


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
    return SimpleNamespace(date_range=YearMonths(1999), data=pl.DataFrame(arr))


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
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY).balance
    assert actual == expect


def test_months_balance_total_row(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY).total_row

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
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY).average

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


def test_amount_end(data, amount_start):
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY).amount_end

    assert actual == 175


def test_amount_end_no_data(data):
    data.data = pl.DataFrame()
    actual = YearBalance(data=data, amount_start=0, today=TODAY).amount_end

    assert actual == 0


def test_amount_balance(data, amount_start):
    actual = YearBalance(
        data=data, amount_start=amount_start, today=TODAY
    ).amount_balance

    assert actual == 165


@pytest.mark.parametrize(
    "series, column",
    [
        pytest.param(lambda b: b.income_data, "incomes", id="income_data"),
        pytest.param(lambda b: b.expense_data, "expenses", id="expense_data"),
        pytest.param(lambda b: b.borrow_data, "borrow", id="borrow_data"),
        pytest.param(
            lambda b: b.borrow_return_data, "borrow_return", id="borrow_return_data"
        ),
        pytest.param(lambda b: b.lend_data, "lend", id="lend_data"),
        pytest.param(
            lambda b: b.lend_return_data, "lend_return", id="lend_return_data"
        ),
        pytest.param(lambda b: b.money_flow, "money_flow", id="money_flow"),
    ],
)
def test_balance_series_reads_its_column(data, amount_start, expect, series, column):
    actual = series(YearBalance(data=data, amount_start=amount_start, today=TODAY))

    assert actual == [x[column] for x in expect]


@pytest.mark.parametrize(
    "average, mean",
    [
        pytest.param(lambda b: b.avg_incomes, 90, id="avg_incomes"),
        pytest.param(lambda b: b.avg_expenses, 15, id="avg_expenses"),
    ],
)
def test_avg_is_the_mean_over_months_with_data(data, average, mean):
    actual = average(YearBalance(data=data, amount_start=0, today=TODAY))

    assert actual == mean


@pytest.mark.parametrize(
    "average, column",
    [
        pytest.param(lambda b: b.avg_incomes, "incomes", id="avg_incomes_none"),
        pytest.param(lambda b: b.avg_expenses, "expenses", id="avg_expenses_none"),
    ],
)
def test_avg_of_an_all_zero_column_is_zero(data, average, column):
    data.data = data.data.with_columns(pl.col(column) * 0)

    actual = average(YearBalance(data=data, amount_start=0, today=TODAY))

    assert actual == 0


@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param(date(1999, 2, 1), 1.5, id="current_year"),
        pytest.param(date(2000, 2, 1), 2, id="not_current_year"),
    ],
)
def test_avg_expenses_counts_months_up_to_today(data, today, expect):
    data.data[0, "expenses"] = 1
    data.data[1, "expenses"] = 2
    data.data[2, "expenses"] = 3

    actual = YearBalance(data=data, amount_start=0, today=today).avg_expenses

    assert actual == expect


def test_balance_money_flow_subtracts_account_charged_savings_fees(data, amount_start):
    without_fee = YearBalance(
        data=data, amount_start=amount_start, today=TODAY
    ).money_flow

    fee = [4] + [0] * (len(data.data) - 1)
    data.data = data.data.with_columns(savings_account_fee=pl.Series(fee))
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY)

    assert actual.money_flow == [flow - 4 for flow in without_fee]
    assert actual.amount_end == without_fee[-1] - 4
