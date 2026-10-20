from datetime import date

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ....core.lib.year_boundary import YearBoundary
from ...services.month_filter import FilterItem
from ...services.type_rows import GroupedTypesTable, NameScope

BOUNDARY = YearBoundary(2026, date(2026, 10, 20))
TYPES = [
    {"id": 3, "title": "Gama"},
    {"id": 2, "title": "Beta"},
    {"id": 1, "title": "Alfa"},
]
NAMES = [
    {"id": 22, "title": "Kava", "parent_id": 2, "valid_for": None},
    {"id": 13, "title": "Ryžiai", "parent_id": 1, "valid_for": None},
    {"id": 31, "title": "Tuščias", "parent_id": 3, "valid_for": None},
    {"id": 11, "title": "Obuoliai", "parent_id": 1, "valid_for": None},
    {"id": 21, "title": "Duona", "parent_id": 2, "valid_for": None},
    {"id": 12, "title": "Pienas", "parent_id": 1, "valid_for": None},
]
YEAR = [
    {"pk": 11, "title": "Obuoliai", "sum": 100_00},
    {"pk": 12, "title": "Pienas", "sum": 200_00},
    {"pk": 21, "title": "Duona", "sum": 500_00},
    {"pk": 22, "title": "Kava", "sum": 50_00},
]
LAST_YEAR = [
    {"pk": 11, "title": "Obuoliai", "sum": 250_00},
    {"pk": 12, "title": "Pienas", "sum": 150_00},
    {"pk": 21, "title": "Duona", "sum": 100_00},
    {"pk": 22, "title": "Kava", "sum": 200_00},
]
LAST_DATES = [
    {"pk": 11, "title": "Obuoliai", "date": date(2026, 3, 1)},
    {"pk": 12, "title": "Pienas", "date": date(2026, 5, 1)},
    {"pk": 21, "title": "Duona", "date": date(2026, 2, 1)},
    {"pk": 22, "title": "Kava", "date": date(2026, 9, 1)},
]
YEAR_SCOPE = NameScope("year")
ALL_SCOPE = NameScope("all")


def _table(
    types=TYPES,
    names=NAMES,
    year=YEAR,
    last_year=LAST_YEAR,
    last_dates=LAST_DATES,
    order="",
    scope=YEAR_SCOPE,
):
    return GroupedTypesTable.build(
        types, names, year, last_year, last_dates, order, scope, BOUNDARY
    )


def _shape(table):
    return [(row.title, [name.title for name in row.names]) for row in table.rows]


def _name(pk, title, parent_id, valid_for=None):
    return {"id": pk, "title": title, "parent_id": parent_id, "valid_for": valid_for}


def _sum(pk, title, cents):
    return {"pk": pk, "title": title, "sum": cents}


BY_TITLE = [
    ("Alfa", ["Obuoliai", "Pienas", "Ryžiai"]),
    ("Beta", ["Duona", "Kava"]),
    ("Gama", ["Tuščias"]),
]
BY_THIS_YEAR = [
    ("Beta", ["Duona", "Kava"]),
    ("Alfa", ["Pienas", "Obuoliai", "Ryžiai"]),
    ("Gama", ["Tuščias"]),
]
BY_LAST_YEAR = [
    ("Alfa", ["Obuoliai", "Pienas", "Ryžiai"]),
    ("Beta", ["Kava", "Duona"]),
    ("Gama", ["Tuščias"]),
]
BY_LAST_EXPENSE = [
    ("Beta", ["Kava", "Duona"]),
    ("Alfa", ["Pienas", "Obuoliai", "Ryžiai"]),
    ("Gama", ["Tuščias"]),
]


@pytest.mark.parametrize(
    "order, active, expected",
    [
        ("nonsense", "title", BY_TITLE),
        ("this_year", "this_year", BY_THIS_YEAR),
        ("last_year", "last_year", BY_LAST_YEAR),
        ("share", "share", BY_THIS_YEAR),
        ("last_expense", "last_expense", BY_LAST_EXPENSE),
    ],
    ids=[
        "unknown_key_falls_back_to_title",
        "this_year",
        "last_year",
        "share",
        "last_expense",
    ],
)
def test_a_sort_orders_types_and_keeps_names_inside_their_type(order, active, expected):
    table = _table(order=order)

    assert _shape(table) == expected
    assert table.order == active


def test_a_names_share_is_of_its_type_and_a_types_of_the_year():
    alfa, beta, gama = _table().rows

    assert [row.share for row in (alfa, beta, gama)] == ["35%", "65%", "–"]
    assert [name.share for name in alfa.names] == ["33%", "67%", "–"]
    assert [name.share for name in beta.names] == ["91%", "9%"]


@pytest.mark.parametrize(
    "scope, expected",
    [
        (YEAR_SCOPE, [("Aaa", ""), ("Ccc", "2026")]),
        (ALL_SCOPE, [("Aaa", ""), ("Bbb", "2024"), ("Ccc", "2026")]),
    ],
    ids=["year", "all"],
)
def test_the_name_scope_hides_a_name_limited_to_another_year(scope, expected):
    names = [
        _name(13, "Ccc", 1, 2026),
        _name(12, "Bbb", 1, 2024),
        _name(11, "Aaa", 1),
    ]

    table = _table(
        types=[{"id": 1, "title": "Alfa"}],
        names=names,
        year=[],
        last_year=[],
        last_dates=[],
        scope=scope,
    )

    assert [(name.title, name.year) for name in table.rows[0].names] == expected


@pytest.mark.parametrize("scope", [YEAR_SCOPE, ALL_SCOPE], ids=["year", "all"])
def test_a_types_figures_count_every_name_whatever_the_scope(scope):
    names = [_name(11, "Aaa", 1), _name(12, "Bbb", 1, 2024)]

    table = _table(
        types=[{"id": 1, "title": "Alfa"}],
        names=names,
        year=[_sum(11, "Aaa", 100_00), _sum(12, "Bbb", 300_00)],
        last_year=[_sum(12, "Bbb", 50_00)],
        last_dates=[
            {"pk": 11, "title": "Aaa", "date": date(2026, 1, 5)},
            {"pk": 12, "title": "Bbb", "date": date(2026, 6, 6)},
        ],
        scope=scope,
    )
    alfa = table.rows[0]

    assert (alfa.this_year, alfa.last_year, alfa.last_expense, alfa.share) == (
        "400",
        "50",
        "2026-06-06",
        "100%",
    )
    assert alfa.names[0].share == "25%"


def test_two_names_titled_alike_keep_their_own_figures():
    names = [_name(11, "Kita", 1), _name(21, "Kita", 2)]

    table = _table(
        types=[{"id": 1, "title": "Alfa"}, {"id": 2, "title": "Beta"}],
        names=names,
        year=[_sum(11, "Kita", 100_00), _sum(21, "Kita", 700_00)],
        last_year=[_sum(21, "Kita", 30_00)],
        last_dates=[
            {"pk": 11, "title": "Kita", "date": date(2026, 1, 5)},
            {"pk": 21, "title": "Kita", "date": date(2026, 8, 8)},
        ],
    )
    alfa_kita = table.rows[0].names[0]
    beta_kita = table.rows[1].names[0]

    assert (alfa_kita.this_year, alfa_kita.last_year, alfa_kita.last_expense) == (
        "100",
        "–",
        "2026-01-05",
    )
    assert (beta_kita.this_year, beta_kita.last_year, beta_kita.last_expense) == (
        "700",
        "30",
        "2026-08-08",
    )


@pytest.mark.parametrize(
    "year, last_year, expected",
    [
        (YEAR, LAST_YEAR, ("850", "700", "100%")),
        ([], [], ("–", "–", "–")),
    ],
    ids=["every_type_summed", "empty_year"],
)
def test_the_total_sums_every_type(year, last_year, expected):
    total = _table(year=year, last_year=last_year).total

    assert (total.this_year, total.last_year, total.share) == expected


@given(st.text())
@example("all")
@example("year")
@example("")
def test_a_name_scope_parses_all_and_falls_back_to_the_year(value):
    assert NameScope.parse(value).value == ("all" if value == "all" else "year")


@pytest.mark.parametrize(
    "scope, active",
    [(YEAR_SCOPE, (True, False)), (ALL_SCOPE, (False, True))],
    ids=["year", "all"],
)
def test_the_name_scope_items_link_both_scopes_and_mark_the_open_one(scope, active):
    assert scope.items("/expenses/types/") == [
        FilterItem("Šie metai", "/expenses/types/", active[0]),
        FilterItem("Visi pavadinimai", "/expenses/types/?scope=all", active[1]),
    ]
