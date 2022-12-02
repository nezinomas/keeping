import calendar
import json
import tempfile
from datetime import date

import pytest
from django.test import override_settings
from freezegun import freeze_time

from ...core.exceptions import MethodInvalid
from ..factories import CountFactory
from ..lib.stats import Stats
from ..models import Count


month_days_1999 = [
    (1, 31), (2, 28), (3, 31),
    (4, 30), (5, 31), (6, 30),
    (7, 31), (8, 31), (9, 30),
    (10, 31), (11, 30), (12, 31)
]


month_days_2000 = [
    (1, 31), (2, 29), (3, 31),
    (4, 30), (5, 31), (6, 30),
    (7, 31), (8, 31), (9, 30),
    (10, 31), (11, 30), (12, 31)
]


@pytest.fixture(name="data")
def fixture_data():
    return [
        {'date': date(1999, 12, 3), 'qty': 1.0},
        {'date': date(1999, 2, 1), 'qty': 2.0},
        {'date': date(1999, 1, 15), 'qty': 2.0},
        {'date': date(1999, 1, 8), 'qty': 1.0},
        {'date': date(2000, 1, 8), 'qty': 1.0},
    ]


@pytest.fixture()
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def data_db():
    CountFactory(date=date(1998, 1, 1), quantity=1.0)
    CountFactory(date=date(1999, 12, 3), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 8), quantity=1.0)
    CountFactory(date=date(2000, 1, 8), quantity=1.0)


@pytest.fixture(name="year_stats_expect_empty")
def fixture_year_stats_expect_empty():
    arr = []
    for i in range(1, 13):
        monthlen = calendar.monthrange(1999, i)[1]
        items = [{'y': 0, 'gap': 0} for _ in range(monthlen)]
        arr.append(items)

    return arr


@pytest.fixture(name="year_stats_expect")
def year_stats_expect(year_stats_expect_empty):
    arr = year_stats_expect_empty
    # 1999-01-08
    arr[0][7]['y'] = 1.0
    arr[0][7]['gap'] = 7.0

    # 1999-01-15
    arr[0][14]['y'] = 2.0
    arr[0][14]['gap'] = 7.0

    # 1999-02-01
    arr[1][0]['y'] = 2.0
    arr[1][0]['gap'] = 17.0

    # 1999-12-03
    arr[11][2]['y'] = 1.0
    arr[11][2]['gap'] = 305

    return arr


def test_weekdays():
    actual = Stats.weekdays()

    assert len(actual) == 7
    assert actual[0] == 'Pirmadienis'
    assert actual[6] == 'Sekmadienis'


def test_weekdays_stats(data):
    actual = Stats(year=1999, data=data).weekdays_stats()

    expect = [
        {'weekday': 0, 'count': 2},  # pirmadienis
        {'weekday': 1, 'count': 0},  # antradienis
        {'weekday': 2, 'count': 0},  # treciadienis
        {'weekday': 3, 'count': 0},  # ketvirtadienis
        {'weekday': 4, 'count': 4},  # pentadienis
        {'weekday': 5, 'count': 0},  # šeštadienis
        {'weekday': 6, 'count': 0},  # sekmdadienis
    ]

    assert actual == expect


def test_weekdays_stats_only_thusdays():
    df = [
        {'date': date(2022, 4, 6), 'qty': 1.0},
        {'date': date(2022, 4, 13), 'qty': 2.0},
        {'date': date(2022, 4, 20), 'qty': 10.0},
    ]

    actual = Stats(year=2022, data=df).weekdays_stats()

    expect = [
        {'weekday': 0, 'count': 0},  # pirmadienis
        {'weekday': 1, 'count': 0},  # antradienis
        {'weekday': 2, 'count': 13},  # treciadienis
        {'weekday': 3, 'count': 0},  # ketvirtadienis
        {'weekday': 4, 'count': 0},  # pentadienis
        {'weekday': 5, 'count': 0},  # šeštadienis
        {'weekday': 6, 'count': 0},  # sekmdadienis
    ]

    assert actual == expect


def test_weekdays_stats_all_years(data):
    actual = Stats(data=data).weekdays_stats()

    expect = [
        {'weekday': 0, 'count': 2},  # pirmadienis
        {'weekday': 1, 'count': 0},  # antradienis
        {'weekday': 2, 'count': 0},  # treciadienis
        {'weekday': 3, 'count': 0},  # ketvirtadienis
        {'weekday': 4, 'count': 4},  # pentadienis
        {'weekday': 5, 'count': 1},  # šeštadienis
        {'weekday': 6, 'count': 0},  # sekmdadienis
    ]

    assert actual == expect


def test_weekdays_stats_nodata():
    actual = Stats(year=1999, data=[]).weekdays_stats()

    expect = [
        {'weekday': 0, 'count': 0},  # pirmadienis
        {'weekday': 1, 'count': 0},  # antradienis
        {'weekday': 2, 'count': 0},  # treciadienis
        {'weekday': 3, 'count': 0},  # ketvirtadienis
        {'weekday': 4, 'count': 0},  # pentadienis
        {'weekday': 5, 'count': 0},  # šeštadienis
        {'weekday': 6, 'count': 0},  # sekmdadienis
    ]

    assert actual == expect


def test_months():
    actual = Stats.months()

    assert len(actual) == 12
    assert actual[0] == 'Sausis'
    assert actual[11] == 'Gruodis'


def test_months_stats(data):
    actual = Stats(year=1999, data=data).months_stats()

    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0]

    assert actual == expect


@pytest.mark.django_db
def test_months_stats_db(data_db):
    year = 1999
    qs = Count.objects.sum_by_day(year=year, count_type='count-type')
    actual = Stats(year=year, data=qs).months_stats()

    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    assert actual == expect


@pytest.mark.django_db
def test_months_stats_db_nodata():
    year = 1999
    qs = Count.objects.sum_by_day(year=year, count_type='count-type')
    actual = Stats(year=year, data=qs).months_stats()

    expect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    assert actual == expect


def test_months_stats_nodata():
    actual = Stats(year=1999, data=[]).months_stats()

    expect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    assert actual == expect


@pytest.mark.xfail(raises=MethodInvalid)
def test_year_stats_no_year_provided(data):
    Stats(data=data).year_stats()


def test_year_stats(data, year_stats_expect):
    actual = Stats(year=1999, data=data).year_stats()

    assert actual == year_stats_expect


@pytest.mark.django_db
def test_year_stats_db(year_stats_expect, data_db):
    year = 1999
    qs = Count.objects.sum_by_day(year=year, count_type='count-type')
    actual = Stats(year=year, data=qs).year_stats()

    assert actual == year_stats_expect


def test_year_stats_nodata(year_stats_expect_empty):
    actual = Stats(year=1999, data=[]).year_stats()

    assert actual == year_stats_expect_empty


@pytest.mark.parametrize('month, days', month_days_1999)
def test_year_stats_months_len(month, days):
    actual = Stats(year=1999, data=[]).year_stats()

    assert len(actual[month - 1]) == days


@pytest.mark.parametrize('month, days', month_days_2000)
def test_year_stats_months_len_leap_year(month, days):
    actual = Stats(year=2000, data=[]).year_stats()

    assert len(actual[month - 1]) == days


def test_year_totals(data):
    actual = Stats(year=1999, data=data).year_totals()

    assert actual == 6


@pytest.mark.django_db
@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_year_totals_queryset():
    CountFactory()
    qs = Count.objects.year(1999, count_type='count-type')

    actual = Stats(year=1999, data=qs).year_totals()

    assert actual == 1


def test_year_totals_all_years(data):
    actual = Stats(data=data).year_totals()

    assert actual == {1999: 6.0, 2000: 1.0}


def test_year_totals_year_not_exists_indata(data):
    actual = Stats(year=2010, data=data).year_totals()

    assert actual == 0


def test_year_totals_year_nodata():
    actual = Stats(data=[]).year_totals()

    assert actual == {}


def test_gaps_for_current_year(data):
    data.append({'date': date(1999, 2, 2), 'qty': 1.0})

    actual = Stats(year=1999, data=data).gaps()

    assert json.dumps(actual) == json.dumps({1: 1, 7: 2, 17: 1, 304: 1})


def test_gaps_for_current_year_with_latest(data):
    data.append({'date': date(1999, 2, 2), 'qty': 1.0})

    actual = Stats(year=1999, data=data, past_latest=date(1998, 1, 1)).gaps()

    assert json.dumps(actual) == json.dumps({1: 1, 7: 1, 17: 1, 304: 1, 372: 1})


def test_gaps_for_all_years(data):
    actual = Stats(data=data).gaps()

    assert json.dumps(actual) == json.dumps({7: 2, 17: 1, 36: 1, 305: 1})


def test_gaps_nodata():
    actual = Stats(year=1999, data=[]).gaps()

    assert actual == {}


@freeze_time('1999-1-3')
def test_current_gap_nodata_current_year():
    actual = Stats(year=1999, data=[]).current_gap()

    assert not actual


@pytest.mark.xfail(raises=MethodInvalid)
def test_current_gap_no_year_provided():
    Stats(data=[]).current_gap()


@freeze_time('1999-1-9')
def test_current_gap(data):
    actual = Stats(year=1999, data=data).current_gap()

    assert actual == -328


@freeze_time('2000-1-9')
def test_current_gap_only_one_record():
    data = [{'date': date(2000, 1, 8), 'qty': 1.0}]

    actual = Stats(year=2000, data=data).current_gap()

    assert actual == 1


@freeze_time('2000-1-9')
def test_current_gap_if_user_look_past_records(data):
    actual = Stats(year=1999, data=data).current_gap()

    assert not actual


# ---------------------------------------------------------------------------------------
# chart_calendar
# ---------------------------------------------------------------------------------------
@pytest.fixture(name="chart_calendar_expect_january_nodata")
def fixture_chart_calendar_expect_january_nodata():
    return {
        'name': 'Sausis',
        'keys': ['x', 'y', 'value', 'week', 'date', 'qty', 'gap'],
        'data': [
            [0, 0, 0.0, 4, '1999-01'],
            [0, 1, 0.0, 4, '1999-01'],
            [0, 2, 0.0, 4, '1999-01'],
            [0, 3, 0.0, 4, '1999-01'],
            [0, 4, 0.01, 53, '1999-01-01'],
            [0, 5, 0.02, 53, '1999-01-02'],
            [0, 6, 0.03, 53, '1999-01-03'],
            [1, 0, 0.01, 1, '1999-01-04'],
            [1, 1, 0.01, 1, '1999-01-05'],
            [1, 2, 0.01, 1, '1999-01-06'],
            [1, 3, 0.01, 1, '1999-01-07'],
            [1, 4, 0.01, 1, '1999-01-08'],
            [1, 5, 0.02, 1, '1999-01-09'],
            [1, 6, 0.03, 1, '1999-01-10'],
            [2, 0, 0.01, 2, '1999-01-11'],
            [2, 1, 0.01, 2, '1999-01-12'],
            [2, 2, 0.01, 2, '1999-01-13'],
            [2, 3, 0.01, 2, '1999-01-14'],
            [2, 4, 0.01, 2, '1999-01-15'],
            [2, 5, 0.02, 2, '1999-01-16'],
            [2, 6, 0.03, 2, '1999-01-17'],
            [3, 0, 0.01, 3, '1999-01-18'],
            [3, 1, 0.01, 3, '1999-01-19'],
            [3, 2, 0.01, 3, '1999-01-20'],
            [3, 3, 0.01, 3, '1999-01-21'],
            [3, 4, 0.01, 3, '1999-01-22'],
            [3, 5, 0.02, 3, '1999-01-23'],
            [3, 6, 0.03, 3, '1999-01-24'],
            [4, 0, 0.01, 4, '1999-01-25'],
            [4, 1, 0.01, 4, '1999-01-26'],
            [4, 2, 0.01, 4, '1999-01-27'],
            [4, 3, 0.01, 4, '1999-01-28'],
            [4, 4, 0.01, 4, '1999-01-29'],
            [4, 5, 0.02, 4, '1999-01-30'],
            [4, 6, 0.03, 4, '1999-01-31'],
        ]
    }


@pytest.fixture(name="chart_calendar_expect_february_nodata")
def fixture_chart_calendar_expect_february_nodata():
    return {
        'name': 'Vasaris',
        'keys': ['x', 'y', 'value', 'week', 'date', 'qty', 'gap'],
        'data': [
            [6, 0, 0.01, 5, '1999-02-01'],
            [6, 1, 0.01, 5, '1999-02-02'],
            [6, 2, 0.01, 5, '1999-02-03'],
            [6, 3, 0.01, 5, '1999-02-04'],
            [6, 4, 0.01, 5, '1999-02-05'],
            [6, 5, 0.02, 5, '1999-02-06'],
            [6, 6, 0.03, 5, '1999-02-07'],
            [7, 0, 0.01, 6, '1999-02-08'],
            [7, 1, 0.01, 6, '1999-02-09'],
            [7, 2, 0.01, 6, '1999-02-10'],
            [7, 3, 0.01, 6, '1999-02-11'],
            [7, 4, 0.01, 6, '1999-02-12'],
            [7, 5, 0.02, 6, '1999-02-13'],
            [7, 6, 0.03, 6, '1999-02-14'],
            [8, 0, 0.01, 7, '1999-02-15'],
            [8, 1, 0.01, 7, '1999-02-16'],
            [8, 2, 0.01, 7, '1999-02-17'],
            [8, 3, 0.01, 7, '1999-02-18'],
            [8, 4, 0.01, 7, '1999-02-19'],
            [8, 5, 0.02, 7, '1999-02-20'],
            [8, 6, 0.03, 7, '1999-02-21'],
            [9, 0, 0.01, 8, '1999-02-22'],
            [9, 1, 0.01, 8, '1999-02-23'],
            [9, 2, 0.01, 8, '1999-02-24'],
            [9, 3, 0.01, 8, '1999-02-25'],
            [9, 4, 0.01, 8, '1999-02-26'],
            [9, 5, 0.02, 8, '1999-02-27'],
            [9, 6, 0.03, 8, '1999-02-28'],
        ]
    }


@pytest.fixture(name="chart_calendar_expect_january_withdata")
def fixture_chart_calendar_expect_january_withdata(chart_calendar_expect_january_nodata):
    chart_calendar_expect_january_nodata['data'][11].append(1.0) #1999-01-08 qty
    chart_calendar_expect_january_nodata['data'][11].append(7.0) #1999-01-08 gap
    chart_calendar_expect_january_nodata['data'][11][2] = 1.0


    chart_calendar_expect_january_nodata['data'][18].append(2.0) #1999-01-15 qty
    chart_calendar_expect_january_nodata['data'][18].append(7.0) #1999-01-15 gap
    chart_calendar_expect_january_nodata['data'][18][2] = 2.0

    return chart_calendar_expect_january_nodata


@pytest.mark.xfail(raises=MethodInvalid)
def test_chart_calendar_no_year_provided():
    Stats(data=[]).chart_calendar()


def test_chart_calendar(data, chart_calendar_expect_january_withdata):
    actual = Stats(year=1999, data=data).chart_calendar()

    assert actual[0] == chart_calendar_expect_january_withdata


@pytest.mark.django_db
def test_chart_calendar_db(chart_calendar_expect_january_withdata, data_db):
    year = 1999
    qs = Count.objects.sum_by_day(year=year, count_type='count-type')
    actual = Stats(year=year, data=qs).chart_calendar()

    assert actual[0] == chart_calendar_expect_january_withdata


def test_chart_calendar_nodata(chart_calendar_expect_january_nodata):
    actual = Stats(year=1999, data=[]).chart_calendar()

    assert actual[0] == chart_calendar_expect_january_nodata


def test_chart_calendar_nodata_february(chart_calendar_expect_february_nodata):
    actual = Stats(year=1999, data=[]).chart_calendar()

    assert actual[1] == chart_calendar_expect_february_nodata


@freeze_time('1999-01-02')
def test_chart_calendar_current_day_nodata(chart_calendar_expect_january_nodata):
    chart_calendar_expect_january_nodata['data'][5][2] = 0.05

    actual = Stats(year=1999, data=[]).chart_calendar()

    assert actual[0] == chart_calendar_expect_january_nodata


@freeze_time('1999-01-01')
def test_chart_calendar_first_day_of_year_with_record(chart_calendar_expect_january_nodata):
    data = [{'date': date(1999, 1, 1), 'qty': 1.0},]

    chart_calendar_expect_january_nodata['data'][4].append(1.0) #1999-01-08 qty
    chart_calendar_expect_january_nodata['data'][4].append(0) #1999-01-08 gap
    chart_calendar_expect_january_nodata['data'][4][2] = 1.0

    actual = Stats(year=1999, data=data).chart_calendar()

    assert actual[0] == chart_calendar_expect_january_nodata
