from datetime import date

import pytest

from ...lib.day_stats import GapSpan, Stats


def in_year(rows, year):
    return [row for row in rows if row["date"].year == year]


@pytest.fixture(name="data")
def fixture_data():
    return [
        {"date": date(1999, 12, 3), "qty": 1.0},
        {"date": date(1999, 2, 1), "qty": 2.0},
        {"date": date(1999, 1, 15), "qty": 2.0},
        {"date": date(1999, 1, 8), "qty": 1.0},
        {"date": date(2000, 1, 8), "qty": 1.0},
    ]


def test_stats_months_list():
    actual = Stats.months()
    assert len(actual) == 12
    assert actual[0] == "Sausis"
    assert actual[11] == "Gruodis"


def test_stats_weekdays_list():
    actual = Stats.weekdays()
    assert len(actual) == 7
    assert actual[0] == "Pirmadienis"
    assert actual[6] == "Sekmadienis"


@pytest.mark.parametrize(
    "years, expect",
    [
        pytest.param(
            (1999,),
            [2, 0, 0, 0, 4, 0, 0],
            id="one_year",
        ),
        pytest.param(
            (1999, 2000),
            [2, 0, 0, 0, 4, 1, 0],
            id="all_years",
        ),
        pytest.param((), [0] * 7, id="empty"),
    ],
)
def test_stats_weekdays_aggregation(data, years, expect):
    rows = [row for row in data if row["date"].year in years]

    actual = Stats(data=rows).weekdays_stats()

    assert actual == [{"weekday": day, "count": n} for day, n in enumerate(expect)]


@pytest.mark.parametrize(
    "years, expect",
    [
        pytest.param(
            (1999,),
            [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0],
            id="one_year",
        ),
        pytest.param((), [0.0] * 12, id="empty"),
    ],
)
def test_stats_months_aggregation(data, years, expect):
    rows = [row for row in data if row["date"].year in years]

    assert Stats(data=rows).months_stats() == expect


@pytest.mark.parametrize(
    "year, expect",
    [pytest.param(1999, 6, id="year"), pytest.param(2010, 0, id="missing_year")],
)
def test_stats_year_total_sums_the_rows_it_is_handed(data, year, expect):
    assert Stats(data=in_year(data, year)).year_total() == expect


@pytest.mark.parametrize(
    "years, expect",
    [
        pytest.param((1999, 2000), {1999: 6.0, 2000: 1.0}, id="two_years"),
        pytest.param((), {}, id="empty"),
    ],
)
def test_stats_totals_by_year(data, years, expect):
    rows = [row for row in data if row["date"].year in years]

    assert Stats(data=rows).totals_by_year() == expect


def test_stats_gap_by_date_measures_each_record_from_the_one_before(data):
    data.append({"date": date(1999, 2, 2), "qty": 1.0})
    actual = Stats(data=in_year(data, 1999)).gap_by_date()
    assert actual[date(1999, 1, 8)] == 7
    assert actual[date(1999, 2, 2)] == 1
    assert actual[date(1999, 12, 3)] == 304


def test_stats_gap_by_date_with_past_latest(data):
    actual = Stats(data=in_year(data, 1999), past_latest=date(1998, 1, 1)).gap_by_date()
    assert actual[date(1999, 1, 8)] == 372


def test_stats_gap_spans_open_on_past_latest(data):
    actual = Stats(data=in_year(data, 1999), past_latest=date(1998, 1, 1)).gap_spans()

    assert actual[0] == GapSpan(date(1998, 1, 1), date(1999, 1, 8), 372)
    assert actual[1] == GapSpan(date(1999, 1, 8), date(1999, 1, 15), 7)


def test_stats_gap_by_date_empty():
    assert Stats(data=[]).gap_by_date() == {}


def test_stats_needs_its_data():
    with pytest.raises(TypeError):
        Stats()


def test_stats_reads_every_year_it_is_handed(data):
    with pytest.raises(TypeError):
        Stats(data=data, year=1999)

    assert Stats(data=data).totals_by_year() == {1999: 6.0, 2000: 1.0}
