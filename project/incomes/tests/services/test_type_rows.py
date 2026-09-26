from datetime import date

from ...services.type_rows import TypesTable

TYPES = [
    {"id": 3, "title": "Kita"},
    {"id": 1, "title": "Freelance"},
    {"id": 2, "title": "Dividendai"},
    {"id": 4, "title": "Alga"},
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


def _table(year=YEAR, order=""):
    return TypesTable.build(TYPES, year, LAST_YEAR, LAST_DATES, order)


def _titles(order):
    return [row.title for row in _table(order=order).rows]


def test_rows_run_by_title_by_default():
    assert _titles("") == ["Alga", "Dividendai", "Freelance", "Kita"]


def test_figures_sort_biggest_first_with_empty_rows_last():
    assert _titles("this_year") == ["Alga", "Freelance", "Dividendai", "Kita"]
    assert _titles("share") == ["Alga", "Freelance", "Dividendai", "Kita"]
    assert _titles("last_year") == ["Alga", "Dividendai", "Freelance", "Kita"]


def test_the_last_income_sorts_newest_first():
    assert _titles("last_income") == ["Alga", "Freelance", "Dividendai", "Kita"]


def test_the_table_names_its_active_column():
    assert (_table().order, _table(order="share").order) == ("title", "share")


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
