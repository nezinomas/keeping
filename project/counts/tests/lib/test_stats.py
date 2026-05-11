import tempfile
from datetime import date

import pytest
from django.test import override_settings

from ...lib.stats import Stats
from ...services.model_services import CountModelService
from ..factories import CountFactory


@pytest.fixture(name="data")
def fixture_data():
    return [
        {"date": date(1999, 12, 3), "qty": 1.0},
        {"date": date(1999, 2, 1), "qty": 2.0},
        {"date": date(1999, 1, 15), "qty": 2.0},
        {"date": date(1999, 1, 8), "qty": 1.0},
        {"date": date(2000, 1, 8), "qty": 1.0},
    ]


@pytest.fixture(name="data_db")
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def fixture_data_db():
    CountFactory(date=date(1998, 1, 1), quantity=1.0)
    CountFactory(date=date(1999, 12, 3), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 8), quantity=1.0)
    CountFactory(date=date(2000, 1, 8), quantity=1.0)


# -------------------------------------------------------------------------------------
# Static / Metadata Methods
# -------------------------------------------------------------------------------------


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


# -------------------------------------------------------------------------------------
# Basic Statistics
# -------------------------------------------------------------------------------------


def test_stats_number_of_records(data):
    stats = Stats(year=1999, data=data)
    assert stats.number_of_records == 6.0


def test_stats_number_of_records_fallback_to_shape(data):
    # Data without 'qty' or 'quantity' column
    incomplete_data = [{"date": date(1999, 1, 1), "other": 1.0}]
    stats = Stats(data=incomplete_data)
    assert stats.number_of_records == 1


def test_stats_prepare_dataframe_renames_quantity():
    data = [{"date": date(1999, 1, 1), "quantity": 1.0}]
    stats = Stats(data=data)
    assert "qty" in stats._df.columns
    assert stats._df["qty"][0] == 1.0


def test_stats_weekdays_aggregation(data):
    actual = Stats(year=1999, data=data).weekdays_stats()
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
    actual = Stats(year=1999, data=[]).weekdays_stats()
    assert len(actual) == 7
    assert all(x["count"] == 0 for x in actual)


def test_stats_months_aggregation(data):
    actual = Stats(year=1999, data=data).months_stats()
    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0]
    assert actual == expect


def test_stats_months_aggregation_empty():
    actual = Stats(year=1999, data=[]).months_stats()
    assert actual == [0.0] * 12


@pytest.mark.django_db
def test_stats_months_aggregation_from_db(main_user, data_db):
    year = 1999
    qs = CountModelService(main_user).sum_by_day(year=year, count_type="count-type")
    actual = Stats(year=year, data=qs).months_stats()
    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    assert actual == expect


def test_stats_year_totals_single_year(data):
    actual = Stats(year=1999, data=data).year_totals()
    assert actual == 6


def test_stats_year_totals_multi_year(data):
    actual = Stats(data=data).year_totals()
    assert actual == {1999: 6.0, 2000: 1.0}


def test_stats_year_totals_missing_year(data):
    actual = Stats(year=2010, data=data).year_totals()
    assert actual == 0


def test_stats_year_totals_empty():
    assert Stats(data=[]).year_totals() == {}
    assert Stats(year=1999, data=[]).year_totals() == 0


# -------------------------------------------------------------------------------------
# Gap Analysis
# -------------------------------------------------------------------------------------


def test_stats_gaps_standard(data):
    data.append({"date": date(1999, 2, 2), "qty": 1.0})
    actual = Stats(year=1999, data=data).gaps()
    assert actual == {1: 1, 7: 2, 17: 1, 304: 1}


def test_stats_gaps_with_past_latest(data):
    data.append({"date": date(1999, 2, 2), "qty": 1.0})
    actual = Stats(year=1999, data=data, past_latest=date(1998, 1, 1)).gaps()
    assert actual == {1: 1, 7: 1, 17: 1, 304: 1, 372: 1}


def test_stats_gaps_empty():
    assert Stats(year=1999, data=[]).gaps() == {}
