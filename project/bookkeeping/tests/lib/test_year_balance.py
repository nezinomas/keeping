from datetime import date
from itertools import accumulate
from types import SimpleNamespace

import polars as pl
import pytest
from hypothesis import example, given
from hypothesis import strategies as st

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


MONTHLY = [
    "incomes",
    "expenses",
    "savings",
    "savings_close",
    "borrow",
    "borrow_return",
    "lend",
    "lend_return",
]
YEAR = st.lists(st.integers(0, 1000), min_size=12, max_size=12)
YEAR_OF_COLUMNS = st.fixed_dictionaries({column: YEAR for column in MONTHLY})
FIXTURE_YEAR = {
    "incomes": [55, 125] + [0] * 10,
    "expenses": [15] + [0] * 11,
    "savings": [1] + [0] * 11,
    "savings_close": [5] + [0] * 11,
    "borrow": [25] + [0] * 11,
    "borrow_return": [15] + [0] * 11,
    "lend": [10] + [0] * 11,
    "lend_return": [5] + [0] * 11,
}


@given(columns=YEAR_OF_COLUMNS, amount_start=st.integers(-1000, 1000))
@example(columns=FIXTURE_YEAR, amount_start=1)
def test_balance_series_read_their_column_and_money_flow_runs_from_the_start(
    columns, amount_start
):
    frame = pl.DataFrame(
        {"date": [date(1999, month, 1) for month in range(1, 13)]} | columns
    )
    balance = YearBalance(
        data=SimpleNamespace(date_range=YearMonths(1999), data=frame),
        amount_start=amount_start,
        today=TODAY,
    )
    net = [
        columns["incomes"][i]
        - columns["expenses"][i]
        + columns["savings_close"][i]
        + columns["borrow"][i]
        + columns["lend_return"][i]
        - columns["savings"][i]
        - columns["borrow_return"][i]
        - columns["lend"][i]
        for i in range(12)
    ]

    actual = {
        "incomes": balance.income_data,
        "expenses": balance.expense_data,
        "borrow": balance.borrow_data,
        "borrow_return": balance.borrow_return_data,
        "lend": balance.lend_data,
        "lend_return": balance.lend_return_data,
        "money_flow": balance.money_flow,
    }

    assert actual == {
        "incomes": columns["incomes"],
        "expenses": columns["expenses"],
        "borrow": columns["borrow"],
        "borrow_return": columns["borrow_return"],
        "lend": columns["lend"],
        "lend_return": columns["lend_return"],
        "money_flow": list(accumulate(net, initial=amount_start))[1:],
    }


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
