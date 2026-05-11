import tempfile
from datetime import date

import pytest
import time_machine
from django.test import override_settings

from ....core.exceptions import MethodInvalidError
from ...lib.stats import Calendar, Stats
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
    CountFactory(date=date(1999, 12, 3), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 8), quantity=1.0)


@pytest.fixture(name="january_nodata_expect")
def fixture_january_nodata_expect():
    return {
        "name": "Sausis",
        "keys": ["x", "y", "value", "week", "date", "qty", "gap"],
        "data": [
            [0, 0, 0, 4, "1999-01"],
            [0, 1, 0, 4, "1999-01"],
            [0, 2, 0, 4, "1999-01"],
            [0, 3, 0, 4, "1999-01"],
            [0, 4, 0.0001, 53, "1999-01-01"],
            [0, 5, 0.0002, 53, "1999-01-02"],
            [0, 6, 0.0003, 53, "1999-01-03"],
            [1, 0, 0.0001, 1, "1999-01-04"],
            [1, 1, 0.0001, 1, "1999-01-05"],
            [1, 2, 0.0001, 1, "1999-01-06"],
            [1, 3, 0.0001, 1, "1999-01-07"],
            [1, 4, 0.0001, 1, "1999-01-08"],
            [1, 5, 0.0002, 1, "1999-01-09"],
            [1, 6, 0.0003, 1, "1999-01-10"],
            [2, 0, 0.0001, 2, "1999-01-11"],
            [2, 1, 0.0001, 2, "1999-01-12"],
            [2, 2, 0.0001, 2, "1999-01-13"],
            [2, 3, 0.0001, 2, "1999-01-14"],
            [2, 4, 0.0001, 2, "1999-01-15"],
            [2, 5, 0.0002, 2, "1999-01-16"],
            [2, 6, 0.0003, 2, "1999-01-17"],
            [3, 0, 0.0001, 3, "1999-01-18"],
            [3, 1, 0.0001, 3, "1999-01-19"],
            [3, 2, 0.0001, 3, "1999-01-20"],
            [3, 3, 0.0001, 3, "1999-01-21"],
            [3, 4, 0.0001, 3, "1999-01-22"],
            [3, 5, 0.0002, 3, "1999-01-23"],
            [3, 6, 0.0003, 3, "1999-01-24"],
            [4, 0, 0.0001, 4, "1999-01-25"],
            [4, 1, 0.0001, 4, "1999-01-26"],
            [4, 2, 0.0001, 4, "1999-01-27"],
            [4, 3, 0.0001, 4, "1999-01-28"],
            [4, 4, 0.0001, 4, "1999-01-29"],
            [4, 5, 0.0002, 4, "1999-01-30"],
            [4, 6, 0.0003, 4, "1999-01-31"],
        ],
    }


def test_calendar_error_no_year():
    with pytest.raises(MethodInvalidError):
        Calendar(Stats(data=[])).chart_data()


def test_calendar_full_year_data(data, january_nodata_expect):
    january_nodata_expect["data"][11] += [1.0, 7.0]  # qty, gap
    january_nodata_expect["data"][11][2] = 1.0  # value/color

    january_nodata_expect["data"][18] += [2.0, 7.0]  # qty, gap
    january_nodata_expect["data"][18][2] = 2.0  # value/color

    stats = Stats(year=1999, data=data)
    actual = Calendar(stats).chart_data()
    assert actual[0] == january_nodata_expect


@pytest.mark.django_db
def test_calendar_from_db(january_nodata_expect, data_db, main_user):
    january_nodata_expect["data"][11] += [1.0, 7.0]
    january_nodata_expect["data"][11][2] = 1.0

    january_nodata_expect["data"][18] += [1.0, 7.0]
    january_nodata_expect["data"][18][2] = 1.0

    qs = CountModelService(main_user).sum_by_day(year=1999, count_type="count-type")
    stats = Stats(year=1999, data=qs)
    actual = Calendar(stats).chart_data()
    assert actual[0] == january_nodata_expect


def test_calendar_empty_data(january_nodata_expect):
    stats = Stats(year=1999, data=[])
    actual = Calendar(stats).chart_data()
    assert actual[0] == january_nodata_expect


@time_machine.travel("1999-01-02")
def test_calendar_highlight_today(january_nodata_expect):
    january_nodata_expect["data"][5][2] = 0.0005  # Highlight color

    stats = Stats(year=1999, data=[])
    actual = Calendar(stats).chart_data()
    assert actual[0] == january_nodata_expect


def test_calendar_first_day_of_year_record(january_nodata_expect):
    data = [{"date": date(1999, 1, 1), "qty": 5.0}]

    january_nodata_expect["data"][4] += [5.0, 0]  # qty, gap=0 for first day
    january_nodata_expect["data"][4][2] = 5.0

    stats = Stats(year=1999, data=data)
    actual = Calendar(stats).chart_data()
    assert actual[0] == january_nodata_expect
