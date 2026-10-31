from datetime import date

import pytest

from ...services.type_rows import TypesTable

TYPES = [
    {"id": 3, "title": "Kita"},
    {"id": 1, "title": "Freelance"},
    {"id": 2, "title": "Dividendai"},
    {"id": 4, "title": "Alga"},
]
YEAR = [
    {"pk": 4, "title": "Alga", "sum": 900_000},
    {"pk": 1, "title": "Freelance", "sum": 299_950},
    {"pk": 2, "title": "Dividendai", "sum": 50},
]
LAST_YEAR = [{"pk": 4, "title": "Alga", "sum": 800_000}]
LAST_DATES = [
    {"pk": 4, "title": "Alga", "date": date(2026, 9, 10)},
    {"pk": 1, "title": "Freelance", "date": date(2026, 7, 7)},
    {"pk": 2, "title": "Dividendai", "date": date(2026, 6, 11)},
]


def _table(year=YEAR, order=""):
    return TypesTable.build(TYPES, year, LAST_YEAR, LAST_DATES, order)


def _titles(order):
    return [row.title for row in _table(order=order).rows]


@pytest.mark.parametrize(
    "order, expected",
    [
        ("", ["Alga", "Dividendai", "Freelance", "Kita"]),
        ("this_year", ["Alga", "Freelance", "Dividendai", "Kita"]),
        ("share", ["Alga", "Freelance", "Dividendai", "Kita"]),
        ("last_year", ["Alga", "Dividendai", "Freelance", "Kita"]),
        ("last_income", ["Alga", "Freelance", "Dividendai", "Kita"]),
    ],
    ids=["by_title_by_default", "this_year", "share", "last_year", "last_income"],
)
def test_rows_sort_by_the_asked_column(order, expected):
    assert _titles(order) == expected


@pytest.mark.parametrize(
    "order", ["title", "this_year"], ids=["title_sort", "rows_without_the_figure"]
)
def test_titles_sort_in_the_lithuanian_alphabet(order):
    types = [
        {"id": 1, "title": "Drabužiai"},
        {"id": 2, "title": "Čekiai"},
        {"id": 3, "title": "Cukrus"},
    ]

    table = TypesTable.build(types, [], [], [], order)

    assert [row.title for row in table.rows] == ["Cukrus", "Čekiai", "Drabužiai"]


def test_a_types_share_is_of_the_year():
    assert [row.share for row in _table().rows] == ["75%", "< 1%", "25%", "–"]
