from datetime import date

from ...services.type_rows import TypesTable

TYPES = [
    {"id": 3, "title": "Kita", "type": "other"},
    {"id": 1, "title": "Freelance", "type": "other"},
    {"id": 2, "title": "Dividendai", "type": "dividents"},
    {"id": 4, "title": "Alga", "type": "salary"},
]
YEAR = [
    {"title": "Alga", "sum": 900_000},
    {"title": "Freelance", "sum": 299_950},
    {"title": "Dividendai", "sum": 50},
]
LAST_YEAR = [{"title": "Alga", "sum": 800_000}]
LAST_DATES = [
    {"title": "Alga", "date": date(2026, 9, 10)},
    {"title": "Freelance", "date": date(2026, 7, 7)},
    {"title": "Dividendai", "date": date(2026, 6, 11)},
]


def _table(year=YEAR):
    return TypesTable.build(TYPES, year, LAST_YEAR, LAST_DATES)


def test_rows_run_by_type_kind_then_title():
    assert [row.title for row in _table().rows] == [
        "Alga",
        "Dividendai",
        "Freelance",
        "Kita",
    ]


def test_a_new_type_kind_starts_a_group():
    assert [row.starts_group for row in _table().rows] == [False, True, True, False]


def test_a_row_states_its_type_in_whole_euros():
    alga = _table().rows[0]

    assert (alga.pk, alga.this_year, alga.last_year) == (4, "9.000", "8.000")
    assert (alga.share, alga.last_income) == ("75%", "2026-09-10")


def test_a_type_without_incomes_still_lists_with_dashes():
    kita = _table().rows[3]

    assert (kita.this_year, kita.last_year, kita.share, kita.last_income) == (
        "–",
        "–",
        "–",
        "–",
    )


def test_the_total_sums_each_column():
    total = _table().total

    assert (total.this_year, total.last_year, total.share) == (
        "12.000",
        "8.000",
        "100%",
    )


def test_an_empty_year_totals_to_dashes():
    total = _table(year=[]).total

    assert (total.this_year, total.share) == ("–", "–")


def test_an_unknown_type_kind_sorts_last_instead_of_failing():
    types = [{"id": 9, "title": "Senas", "type": "retired"}, *TYPES]

    table = TypesTable.build(types, YEAR, LAST_YEAR, LAST_DATES)

    assert table.rows[-1].title == "Senas"
