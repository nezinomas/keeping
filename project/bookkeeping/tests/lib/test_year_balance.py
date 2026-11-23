from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest

from ...lib.make_dataframe import YearMonths
from ...lib.year_balance import YearBalance

TODAY = date(2000, 1, 1)


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


def _months():
    """1999's rows: January and February hold figures, every later month zero."""
    first = [
        {
            "incomes": 55,
            "expenses": 15,
            "savings": 1,
            "savings_close": 5,
            "borrow": 25,
            "borrow_return": 15,
            "lend": 10,
            "lend_return": 5,
        },
        {"incomes": 125},
    ]
    return _year_of(*first)


@pytest.fixture(name="data")
def fixture_data():
    return SimpleNamespace(date_range=YearMonths(1999), data=_months())


@pytest.fixture(name="amount_start")
def fixture_amount_start():
    return 1


def _balance_rows():
    """`_months()` with each month's balance and the money flow run from the start."""
    balances = [40, 125] + [0] * 10
    flows = [50] + [175] * 11
    return [
        row | {"balance": balance, "money_flow": flow}
        for row, balance, flow in zip(
            _months().to_dicts(), balances, flows, strict=True
        )
    ]


TOTAL_ROW = {
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


@pytest.mark.parametrize(
    "read, expect",
    [
        pytest.param(lambda b: b.balance, _balance_rows(), id="balance"),
        pytest.param(lambda b: b.total_row, TOTAL_ROW, id="total-row"),
        pytest.param(lambda b: b.amount_end, 175, id="amount-end"),
        pytest.param(lambda b: b.amount_balance, 165, id="amount-balance"),
    ],
)
def test_a_year_balance_reads_its_rows_total_row_and_year_end(
    data, amount_start, read, expect
):
    actual = YearBalance(data=data, amount_start=amount_start, today=TODAY)

    assert read(actual) == expect


@pytest.mark.parametrize(
    "read, expect",
    [
        pytest.param(lambda b: b.amount_end, 0, id="amount-end"),
        pytest.param(lambda b: (b.avg_incomes, b.avg_expenses), (0, 0), id="averages"),
    ],
)
def test_a_year_with_no_rows_ends_at_0_and_averages_0(data, read, expect):
    data.data = pl.DataFrame()

    actual = YearBalance(data=data, amount_start=0, today=TODAY)

    assert read(actual) == expect


def test_months_balance_average(data, amount_start):
    balance = YearBalance(data=data, amount_start=amount_start, today=TODAY)

    # each column's year over twelve months, the year being over
    expect = {column: total / 12 for column, total in TOTAL_ROW.items()}

    assert balance.average == pytest.approx(expect)


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
            [122] + [132] * 11,
            id="every-column-a-different-value",
        ),
        pytest.param(
            0,
            [{"expenses": 7}, {"incomes": 3}, {"lend": 1}],
            [-7, -4] + [-5] * 10,
            id="a-flow-below-zero",
        ),
    ],
)
def test_money_flow_runs_from_the_start_through_every_column(
    amount_start, months, expect
):
    balance = YearBalance(
        data=SimpleNamespace(date_range=YearMonths(1999), data=_year_of(*months)),
        amount_start=amount_start,
        today=TODAY,
    )

    assert balance.money_flow == expect


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
