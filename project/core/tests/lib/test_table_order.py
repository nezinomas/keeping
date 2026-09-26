from datetime import date

from ...lib.table_order import Column, TableOrder

ORDER = TableOrder(
    columns=(Column("title"), Column("sum", descending=True), Column("date")),
    default="title",
)
ROWS = [
    {"title": "Beta", "sum": 5, "date": date(2026, 3, 1)},
    {"title": "Gama"},
    {"title": "Alfa", "sum": 9, "date": date(2026, 1, 1)},
]


def _titles(order):
    return [row["title"] for row in ORDER.sort(order, ROWS, lambda row: row).rows]


def test_an_ascending_column_runs_smallest_first():
    assert _titles("title") == ["Alfa", "Beta", "Gama"]


def test_a_descending_column_runs_biggest_first():
    assert _titles("sum") == ["Alfa", "Beta", "Gama"]


def test_an_absent_value_sorts_last_ascending_too():
    assert _titles("date") == ["Alfa", "Beta", "Gama"]


def test_an_absent_value_sorts_last_descending():
    rows = [{"title": "Gama"}, {"title": "Beta", "sum": 5}]

    ordered = ORDER.sort("sum", rows, lambda row: row)

    assert [row["title"] for row in ordered.rows] == ["Beta", "Gama"]


def test_equal_values_keep_the_order_they_came_in():
    rows = [{"title": "Beta", "sum": 5}, {"title": "Alfa", "sum": 5}]

    ordered = ORDER.sort("sum", rows, lambda row: row)

    assert [row["title"] for row in ordered.rows] == ["Beta", "Alfa"]


def test_the_ordered_rows_name_the_active_column():
    assert ORDER.sort("sum", ROWS, lambda row: row).active == "sum"


def test_an_unknown_or_missing_order_falls_back_to_the_default():
    for order in ("price", ""):
        ordered = ORDER.sort(order, ROWS, lambda row: row)

        assert ordered.active == "title"
        assert [row["title"] for row in ordered.rows] == ["Alfa", "Beta", "Gama"]
