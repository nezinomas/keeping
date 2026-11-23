from types import SimpleNamespace

import pytest

from ...lib import total_rows

_PROFIT_FIELDS = ["incomes", "fee", "market_value", "profit_sum", "profit_proc"]


@pytest.mark.parametrize(
    "data, fields, expect",
    [
        pytest.param(
            [SimpleNamespace(x=111, A=1, B=2), SimpleNamespace(x=222, A=1, B=2)],
            ["A", "B"],
            {"A": 2, "B": 4},
            id="sums_only_the_named_fields",
        ),
        pytest.param([], ["A", "B"], {"A": 0, "B": 0}, id="zero_without_rows"),
        pytest.param(
            [
                SimpleNamespace(incomes=100, sold=0, profit_sum=200),
                SimpleNamespace(incomes=50, sold=100, profit_sum=100),
            ],
            ["incomes", "profit_sum", "sold"],
            {"incomes": 150, "profit_sum": 300, "sold": 100},
            id="a_zero_adds_nothing",
        ),
    ],
)
def test_total_row_sums_each_field(data, fields, expect):
    assert total_rows.total_row(data, fields=fields) == expect


def _fund_row(shows_profit, **values):
    return SimpleNamespace(shows_profit=shows_profit, **values)


def test_funds_total_row_profit_reads_only_the_rows_that_show_one():
    data = [
        _fund_row(True, incomes=100000, fee=0, market_value=110000, profit_sum=10000),
        _fund_row(False, incomes=50000, fee=0, market_value=0, profit_sum=-30000),
    ]

    actual = total_rows.funds_total_row(data, fields=_PROFIT_FIELDS)

    assert actual["profit_sum"] == 10000
    assert actual["profit_proc"] == 10.0


def test_funds_total_row_other_cells_stay_the_column_sum():
    data = [
        _fund_row(True, incomes=100000, fee=5, market_value=110000, profit_sum=10000),
        _fund_row(False, incomes=50000, fee=7, market_value=20000, profit_sum=-30000),
    ]

    actual = total_rows.funds_total_row(data, fields=_PROFIT_FIELDS)

    assert actual["incomes"] == 150000
    assert actual["fee"] == 12
    assert actual["market_value"] == 130000


# the base is what was paid in less what was switched; down to one cent it holds
@pytest.mark.parametrize(
    "switched_within, percent",
    [
        pytest.param(100000, 10000 / 130000 * 100, id="switched"),
        pytest.param(229999, 10000 / 1 * 100, id="a-cent-left"),
    ],
)
def test_funds_total_row_takes_the_switched_money_off_the_shown_base(
    switched_within, percent
):
    data = [
        _fund_row(True, incomes=230000, fee=0, market_value=140000, profit_sum=10000),
    ]

    actual = total_rows.funds_total_row(
        data, fields=_PROFIT_FIELDS, switched_within=switched_within
    )

    assert actual["profit_proc"] == pytest.approx(percent)


@pytest.mark.parametrize("switched_within", [100000, 150000])
def test_funds_total_row_profit_is_zero_when_the_base_is_used_up(switched_within):
    data = [_fund_row(True, incomes=100000, fee=0, market_value=0, profit_sum=30000)]

    actual = total_rows.funds_total_row(
        data, fields=_PROFIT_FIELDS, switched_within=switched_within
    )

    assert actual["profit_proc"] == 0.0


def test_funds_total_row_no_row_shows_a_profit():
    data = [_fund_row(False, incomes=50000, fee=0, market_value=0, profit_sum=-3)]

    actual = total_rows.funds_total_row(data, fields=_PROFIT_FIELDS)

    assert actual["profit_sum"] == 0
    assert actual["profit_proc"] == 0
