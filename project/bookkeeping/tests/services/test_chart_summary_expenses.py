from types import SimpleNamespace

import pytest

from ...services.chart_summary_expenses import ChartSummaryExpensesService

TYPES = [
    {"year": 2000, "sum": 5, "title": "X"},
    {"year": 2002, "sum": 15, "title": "X"},
    {"year": 2001, "sum": 12, "title": "Y"},
    {"year": 2000, "sum": 2, "title": "Y"},
]

NAMES = [
    {"year": 2000, "sum": 5, "title": "X / A"},
    {"year": 2000, "sum": 2, "title": "Y / B"},
    {"year": 2001, "sum": 12, "title": "Y / B"},
    {"year": 2002, "sum": 15, "title": "X / A"},
]


@pytest.mark.parametrize(
    "rows, expect",
    [
        pytest.param(TYPES, [2000, 2001, 2002], id="types"),
        pytest.param(
            [*NAMES, {"year": 1999, "sum": 15, "title": "A", "root": "X"}],
            [1999, 2000, 2001, 2002],
            id="sorting",
        ),
        pytest.param([], [], id="no_data"),
    ],
)
def test_categories(rows, expect):
    obj = ChartSummaryExpensesService(data=SimpleNamespace(data=rows))

    actual = obj.categories

    assert actual == expect


@pytest.mark.parametrize(
    "rows, expect",
    [
        pytest.param(
            TYPES,
            [
                {"name": "X", "data": [5, 0, 15]},
                {"name": "Y", "data": [2, 12, 0]},
            ],
            id="types",
        ),
        pytest.param([], [], id="types_empty"),
        pytest.param(
            NAMES,
            [
                {"name": "X / A", "data": [5, 0, 15]},
                {"name": "Y / B", "data": [2, 12, 0]},
            ],
            id="names",
        ),
        pytest.param(
            TYPES + NAMES,
            [
                {"name": "X", "data": [5, 0, 15]},
                {"name": "X / A", "data": [5, 0, 15]},
                {"name": "Y", "data": [2, 12, 0]},
                {"name": "Y / B", "data": [2, 12, 0]},
            ],
            id="full",
        ),
    ],
)
def test_series_data(rows, expect):
    obj = ChartSummaryExpensesService(data=SimpleNamespace(data=rows))

    actual = obj.series_data

    assert actual == expect


@pytest.mark.parametrize(
    "read, expect",
    [
        pytest.param(lambda o: o.total_col, {"X": 20, "Y": 14}, id="column"),
        pytest.param(lambda o: o.total_row, [7, 12, 15], id="row"),
        pytest.param(lambda o: o.total, 34, id="total"),
    ],
)
def test_series_total(read, expect):
    obj = ChartSummaryExpensesService(data=SimpleNamespace(data=TYPES))

    actual = read(obj)

    assert actual == expect
