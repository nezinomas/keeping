from datetime import date

import pytest

from ...services.type_rows import GroupedTypesTable


def _type(pk, title):
    return {"id": pk, "title": title, "necessary": False}


TYPES = [
    _type(3, "Gama"),
    _type(2, "Beta"),
    _type(1, "Alfa"),
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


def _table(
    types=TYPES,
    names=NAMES,
    year=YEAR,
    last_year=LAST_YEAR,
    last_dates=LAST_DATES,
    order="",
):
    return GroupedTypesTable.build(types, names, year, last_year, last_dates, order)


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
    "order, expected",
    [
        ("", BY_TITLE),
        ("this_year", BY_THIS_YEAR),
        ("last_year", BY_LAST_YEAR),
        ("share", BY_THIS_YEAR),
        ("last_expense", BY_LAST_EXPENSE),
    ],
    ids=["by_title_by_default", "this_year", "last_year", "share", "last_expense"],
)
def test_a_sort_orders_types_and_keeps_names_inside_their_type(order, expected):
    assert _shape(_table(order=order)) == expected


def test_a_names_share_is_of_its_type_and_a_types_of_the_year():
    alfa, beta, gama = _table().rows

    assert [row.share for row in (alfa, beta, gama)] == ["35%", "65%", "–"]
    assert [name.share for name in alfa.names] == ["33%", "67%", "–"]
    assert [name.share for name in beta.names] == ["91%", "9%"]


def test_a_types_figures_count_every_name_whatever_its_year():
    names = [_name(11, "Aaa", 1), _name(12, "Bbb", 1, 2024)]

    table = _table(
        types=[_type(1, "Alfa")],
        names=names,
        year=[_sum(11, "Aaa", 100_00), _sum(12, "Bbb", 300_00)],
        last_year=[_sum(12, "Bbb", 50_00)],
        last_dates=[
            {"pk": 11, "title": "Aaa", "date": date(2026, 1, 5)},
            {"pk": 12, "title": "Bbb", "date": date(2026, 6, 6)},
        ],
    )
    alfa = table.rows[0]

    assert (alfa.this_year, alfa.last_year, alfa.last_date, alfa.share) == (
        "400",
        "50",
        "2026-06-06",
        "100%",
    )
    assert alfa.names[0].share == "25%"


def test_two_names_titled_alike_keep_their_own_figures():
    names = [_name(11, "Kita", 1), _name(21, "Kita", 2)]

    table = _table(
        types=[_type(1, "Alfa"), _type(2, "Beta")],
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

    assert (alfa_kita.this_year, alfa_kita.last_year, alfa_kita.last_date) == (
        "100",
        "–",
        "2026-01-05",
    )
    assert (beta_kita.this_year, beta_kita.last_year, beta_kita.last_date) == (
        "700",
        "30",
        "2026-08-08",
    )


YEARS_APART = [
    _name(14, "Gruzija", 1, 2012),
    _name(11, "Kita", 1),
    _name(13, "Bilietai", 1, 2025),
    _name(15, "Zuikis", 1),
    _name(12, "Aplink", 1, 2025),
]


@pytest.mark.parametrize(
    "order, expected",
    [
        ("title", ["Kita", "Zuikis", "Aplink", "Bilietai", "Gruzija"]),
        ("this_year", ["Bilietai", "Kita", "Aplink", "Gruzija", "Zuikis"]),
    ],
    ids=["title_puts_years_after_newest_first", "a_figure_ties_by_title"],
)
def test_names_order_by_year_under_title_and_by_their_figure_otherwise(order, expected):
    table = _table(
        types=[_type(1, "Kelionės")],
        names=YEARS_APART,
        year=[_sum(11, "Kita", 100_00), _sum(13, "Bilietai", 300_00)],
        last_year=[],
        last_dates=[],
        order=order,
    )

    assert [name.title for name in table.rows[0].names] == expected


def test_types_and_names_read_in_the_lithuanian_alphabet():
    titles = ["Šildymas", "Ypatingos", "Autobusas", "Sveikata", "Jūra"]
    titles += ["Įrankiai", "Telefonas", "Ąžuolas"]
    types = [
        _type(2, "Čekiai"),
        _type(3, "Drabužiai"),
        _type(1, "Cukrus"),
    ]
    names = [_name(10 + i, title, 1) for i, title in enumerate(titles)]

    table = _table(types=types, names=names, year=[], last_year=[], last_dates=[])

    assert [row.title for row in table.rows] == ["Cukrus", "Čekiai", "Drabužiai"]
    assert [name.title for name in table.rows[0].names] == [
        "Autobusas",
        "Ąžuolas",
        "Įrankiai",
        "Ypatingos",
        "Jūra",
        "Sveikata",
        "Šildymas",
        "Telefonas",
    ]
