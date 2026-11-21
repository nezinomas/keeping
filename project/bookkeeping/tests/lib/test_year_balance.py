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
    balance = YearBalance(data=data, amount_start=amount_start, today=TODAY)

    # each column's year over twelve months, the year being over
    expect = {
        "incomes": 15,
        "expenses": 1.25,
        "balance": 13.75,
        "savings": 1 / 12,
        "savings_close": 5 / 12,
        "borrow": 25 / 12,
        "borrow_return": 1.25,
        "lend": 10 / 12,
        "lend_return": 5 / 12,
        "money_flow": 1975 / 12,
    }

    assert balance.average == pytest.approx(expect)
    assert (balance.avg_incomes, balance.avg_expenses) == (15, 1.25)


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


def _year_of(*months):
    """1999 with its first months as given, every other cell zero."""
    given_months = [*months] + [{}] * (12 - len(months))
    return pl.DataFrame(
        [
            {"date": date(1999, month, 1)} | dict.fromkeys(MONTHLY, 0) | cells
            for month, cells in enumerate(given_months, 1)
        ]
    )


@pytest.mark.parametrize(
    "amount_start, months, expect",
    [
        pytest.param(
            -3,
            [
                {
                    "incomes": 100,
                    "expenses": 1,
                    "savings": 2,
                    "savings_close": 4,
                    "borrow": 8,
                    "borrow_return": 16,
                    "lend": 32,
                    "lend_return": 64,
                },
                {"incomes": 10},
            ],
            {
                "borrow": [8] + [0] * 11,
                "borrow_return": [16] + [0] * 11,
                "lend": [32] + [0] * 11,
                "lend_return": [64] + [0] * 11,
                "money_flow": [122] + [132] * 11,
            },
            id="every-column-a-different-value",
        ),
        pytest.param(
            0,
            [{"expenses": 7}, {"incomes": 3}, {"lend": 1}],
            {
                "borrow": [0] * 12,
                "borrow_return": [0] * 12,
                "lend": [0, 0, 1] + [0] * 9,
                "lend_return": [0] * 12,
                "money_flow": [-7, -4] + [-5] * 10,
            },
            id="a-flow-below-zero",
        ),
    ],
)
def test_balance_series_read_their_column_and_money_flow_runs_from_the_start(
    amount_start, months, expect
):
    balance = YearBalance(
        data=SimpleNamespace(date_range=YearMonths(1999), data=_year_of(*months)),
        amount_start=amount_start,
        today=TODAY,
    )

    actual = {
        "borrow": balance.borrow_data,
        "borrow_return": balance.borrow_return_data,
        "lend": balance.lend_data,
        "lend_return": balance.lend_return_data,
        "money_flow": balance.money_flow,
    }

    assert actual == expect


def test_averages_of_a_year_with_no_rows_are_zero(data):
    data.data = pl.DataFrame()

    balance = YearBalance(data=data, amount_start=0, today=TODAY)

    assert (balance.avg_incomes, balance.avg_expenses) == (0, 0)


# 180 in over January and February; 1, 2 and 3 out, March's left out until reached
@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param(date(1999, 2, 1), (90, 1.5), id="running-of-two"),
        pytest.param(date(2000, 2, 1), (15, 0.5), id="past-of-twelve"),
        pytest.param(date(1998, 2, 1), (0, 0), id="not-begun"),
    ],
)
def test_averages_divide_by_the_months_the_year_has_reached(data, today, expect):
    data.data[0, "expenses"] = 1
    data.data[1, "expenses"] = 2
    data.data[2, "expenses"] = 3

    balance = YearBalance(data=data, amount_start=0, today=today)

    assert (balance.avg_incomes, balance.avg_expenses) == expect


def test_balance_money_flow_subtracts_account_charged_savings_fees(data, amount_start):
    without_fee = YearBalance(
        data=data, amount_start=amount_start, today=TODAY
    ).money_flow

    fee = [4] + [0] * (len(data.data) - 1)
    data.data = data.data.with_columns(savings_account_fee=pl.Series(fee))
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY)

    assert actual.money_flow == [flow - 4 for flow in without_fee]
    assert actual.amount_end == without_fee[-1] - 4


@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param(date(1998, 12, 1), True, id="coming"),
        pytest.param(date(1999, 2, 1), False, id="current"),
    ],
)
def test_year_balance_knows_a_coming_year(data, today, expect):
    actual = YearBalance(data=data, amount_start=0, today=today).is_coming

    assert actual is expect
