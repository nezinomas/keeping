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


# Static / Metadata Methods


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


# Basic Statistics


def test_stats_prepare_dataframe_renames_quantity():
    data = [{"date": date(1999, 1, 1), "quantity": 1.0}]
    stats = Stats(data=data)
    assert "qty" in stats._df.columns
    assert stats._df["qty"][0] == 1.0


def test_stats_weekdays_aggregation(data):
    actual = Stats(data=in_year(data, 1999)).weekdays_stats()
    expect = [
        {"weekday": 0, "count": 2},  # pirmadienis
        {"weekday": 1, "count": 0},
        {"weekday": 2, "count": 0},
        {"weekday": 3, "count": 0},
        {"weekday": 4, "count": 4},
        {"weekday": 5, "count": 0},
        {"weekday": 6, "count": 0},
    ]
    assert actual == expect


def test_stats_weekdays_aggregation_all_years(data):
    actual = Stats(data=data).weekdays_stats()
    expect = [
        {"weekday": 0, "count": 2},
        {"weekday": 1, "count": 0},
        {"weekday": 2, "count": 0},
        {"weekday": 3, "count": 0},
        {"weekday": 4, "count": 4},
        {"weekday": 5, "count": 1},
        {"weekday": 6, "count": 0},
    ]
    assert actual == expect


def test_stats_weekdays_aggregation_empty():
    actual = Stats(data=[]).weekdays_stats()
    assert len(actual) == 7
    assert all(x["count"] == 0 for x in actual)


def test_stats_months_aggregation(data):
    actual = Stats(data=in_year(data, 1999)).months_stats()
    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0]
    assert actual == expect


def test_stats_months_aggregation_empty():
    actual = Stats(data=[]).months_stats()
    assert actual == [0.0] * 12


def test_stats_year_total(data):
    actual = Stats(data=in_year(data, 1999)).year_total()
    assert actual == 6


def test_stats_year_total_missing_year(data):
    actual = Stats(data=in_year(data, 2010)).year_total()
    assert actual == 0


def test_stats_year_total_empty():
    assert Stats(data=[]).year_total() == 0


def test_stats_totals_by_year(data):
    actual = Stats(data=data).totals_by_year()
    assert actual == {1999: 6.0, 2000: 1.0}


def test_stats_totals_by_year_empty():
    assert Stats(data=[]).totals_by_year() == {}


# Gap Analysis


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
