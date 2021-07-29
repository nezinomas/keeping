import calendar
import json
from datetime import date

import pytest
from freezegun import freeze_time
from mock import patch

from ...core.exceptions import MethodInvalid
from ..apps import App_name
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


@pytest.fixture()
def _data():
    df = [
        {'date': date(1999, 12, 3), 'qty': 1.0},
        {'date': date(1999, 2, 1), 'qty': 2.0},
        {'date': date(1999, 1, 15), 'qty': 2.0},
        {'date': date(1999, 1, 8), 'qty': 1.0},
        {'date': date(2000, 1, 8), 'qty': 1.0},
    ]
    return df


@pytest.fixture()
def _data_db():
    CountFactory(date=date(1999, 12, 3), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 2, 1), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 15), quantity=1.0)
    CountFactory(date=date(1999, 1, 8), quantity=1.0)
    CountFactory(date=date(2000, 1, 8), quantity=1.0)


@pytest.fixture()
def _year_stats_expect_empty():
    arr = []
    for i in range(1, 13):
        monthlen = calendar.monthlen(1999, i)
        items = []
        for _ in range(0, monthlen):
            items.append({'y': 0, 'gap': 0})
        arr.append(items)

    return arr


@pytest.fixture()
def _year_stats_expect(_year_stats_expect_empty):
    arr = _year_stats_expect_empty
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


def test_weekdays_stats(_data):
    actual = Stats(year=1999, data=_data).weekdays_stats()

    expect = [
        {'weekday': 0, 'count': 1},  # pirmadienis
        {'weekday': 1, 'count': 0},  # antradienis
        {'weekday': 2, 'count': 0},  # treciadienis
        {'weekday': 3, 'count': 0},  # ketvirtadienis
        {'weekday': 4, 'count': 3},  # pentadienis
        {'weekday': 5, 'count': 0},  # šeštadienis
        {'weekday': 6, 'count': 0},  # sekmdadienis
    ]

    assert actual == expect


def test_weekdays_stats_all_years(_data):
    actual = Stats(data=_data).weekdays_stats()

    expect = [
        {'weekday': 0, 'count': 1},  # pirmadienis
        {'weekday': 1, 'count': 0},  # antradienis
        {'weekday': 2, 'count': 0},  # treciadienis
        {'weekday': 3, 'count': 0},  # ketvirtadienis
        {'weekday': 4, 'count': 3},  # pentadienis
        {'weekday': 5, 'count': 1},  # šeštadienis
        {'weekday': 6, 'count': 0},  # sekmdadienis
    ]

    assert actual == expect


def test_weekdays_stats_no_data():
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


def test_months_stats(_data):
    actual = Stats(year=1999, data=_data).months_stats()

    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    assert actual == expect


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_months_stats_db(_data_db):
    year = 1999
    qs = Count.objects.sum_by_day(year=year)
    actual = Stats(year=year, data=qs).months_stats()

    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    assert actual == expect


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_months_stats_db_no_data():
    year = 1999
    qs = Count.objects.sum_by_day(year=year)
    actual = Stats(year=year, data=qs).months_stats()

    expect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    assert actual == expect


def test_months_stats_no_data():
    actual = Stats(year=1999, data=[]).months_stats()

    expect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    assert actual == expect


@pytest.mark.xfail(raises=MethodInvalid)
def test_year_stats_no_year_provided(_data):
    Stats(data=_data).year_stats()


def test_year_stats(_data, _year_stats_expect):
    actual = Stats(year=1999, data=_data).year_stats()

    assert actual == _year_stats_expect


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_year_stats_db(_year_stats_expect, _data_db):
    year = 1999
    qs = Count.objects.sum_by_day(year=year)
    actual = Stats(year=year, data=qs).year_stats()
    # assert 0
    assert actual == _year_stats_expect


def test_year_stats_no_data(_year_stats_expect_empty):
    actual = Stats(year=1999, data=[]).year_stats()

    assert actual == _year_stats_expect_empty


@pytest.mark.parametrize('month, days', month_days_1999)
def test_year_stats_months_len(month, days):
    actual = Stats(year=1999, data=[]).year_stats()

    assert len(actual[month - 1]) == days


@pytest.mark.parametrize('month, days', month_days_2000)
def test_year_stats_months_len_leap_year(month, days):
    actual = Stats(year=2000, data=[]).year_stats()

    assert len(actual[month - 1]) == days


def test_year_totals(_data):
    actual = Stats(year=1999, data=_data).year_totals()

    assert actual == 6


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_year_totals_queryset():
    CountFactory()
    qs = Count.objects.year(1999)

    actual = Stats(year=1999, data=qs).year_totals()

    assert actual == 1


def test_year_totals_all_years(_data):
    actual = Stats(data=_data).year_totals()

    assert actual == {1999: 6.0, 2000: 1.0}


def test_year_totals_year_not_exists_in_data(_data):
    actual = Stats(year=2010, data=_data).year_totals()

    assert actual == 0


def test_year_totals_year_no_data():
    actual = Stats(data=[]).year_totals()

    assert actual == {}


def test_month_days_len():
    actual = Stats(year=1999, data=[]).month_days()

    assert len(actual) == 12


@pytest.mark.parametrize('month, days', month_days_1999)
def test_month_days(month, days):
    actual = Stats(year=1999, data=[]).month_days()

    assert len(actual[month - 1]) == days

    for day in range(0, days):
        assert actual[month - 1][day] == day + 1


@pytest.mark.xfail(raises=MethodInvalid)
def test_year_month_days_no_year_provided():
    Stats(data=[]).month_days()


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_items():
    CountFactory()
    qs = Count.objects.year(1999)

    actual = Stats(year=1999, data=qs).items()

    assert len(actual) == 1

    actual = actual[0]

    assert actual['quantity'] == 1
    assert actual['date'] == date(1999, 1, 1)


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_items_odering():
    CountFactory(date=date(1999, 1, 1))
    CountFactory(date=date(1999, 12, 31))

    qs = Count.objects.year(1999)

    actual = Stats(year=1999, data=qs).items()

    assert actual[0]['date'] == date(1999, 12, 31)
    assert actual[1]['date'] == date(1999, 1, 1)


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_items_no_data():
    qs = Count.objects.year(1999)

    actual = Stats(year=1999, data=qs).items()

    assert actual == []


def test_gaps_for_current_year(_data):
    _data.append({'date': date(1999, 2, 2), 'qty': 1.0})

    actual = Stats(year=1999, data=_data).gaps()

    assert json.dumps(actual) == json.dumps({1: 1, 7: 2, 17: 1, 304: 1})


def test_gaps_for_all_years(_data):
    actual = Stats(data=_data).gaps()

    assert json.dumps(actual) == json.dumps({7: 2, 17: 1, 36: 1, 305: 1})


def test_gaps_no_data():
    actual = Stats(year=1999, data=[]).gaps()

    assert actual == {}


@freeze_time('1999-1-3')
def test_current_gap_no_data_current_year():
    actual = Stats(year=1999, data=[]).current_gap()

    assert not actual


@pytest.mark.xfail(raises=MethodInvalid)
def test_current_gap_no_year_provided():
    Stats(data=[]).current_gap()


@freeze_time('1999-1-9')
def test_current_gap(_data):
    actual = Stats(year=1999, data=_data).current_gap()

    assert actual == -328


@freeze_time('2000-1-9')
def test_current_gap_only_one_record():
    _data = [{'date': date(2000, 1, 8), 'qty': 1.0}]

    actual = Stats(year=2000, data=_data).current_gap()

    assert actual == 1


@freeze_time('2000-1-9')
def test_current_gap_if_user_look_past_records(_data):
    actual = Stats(year=1999, data=_data).current_gap()

    assert not actual


# ---------------------------------------------------------------------------------------
# chart_calendar
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _chart_calendar_expect_january_no_data():
    arr = {
        'name': 'Sausis',
        'keys': ['x', 'y', 'value', 'week', 'date', 'qty', 'gap'],
        'data': [
            [0, 0, 0, 1, 'None'],
            [0, 1, 0, 1, 'None'],
            [0, 2, 0, 1, 'None'],
            [0, 3, 0, 1, 'None'],
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

    return arr


@pytest.fixture
def _chart_calendar_expect_january_with_data(_chart_calendar_expect_january_no_data):
    _chart_calendar_expect_january_no_data['data'][11].append(1.0) #1999-01-08 qty
    _chart_calendar_expect_january_no_data['data'][11].append(7.0) #1999-01-08 gap
    _chart_calendar_expect_january_no_data['data'][11][2] = 1.0


    _chart_calendar_expect_january_no_data['data'][18].append(2.0) #1999-01-15 qty
    _chart_calendar_expect_january_no_data['data'][18].append(7.0) #1999-01-15 gap
    _chart_calendar_expect_january_no_data['data'][18][2] = 2.0

    return _chart_calendar_expect_january_no_data


@pytest.mark.xfail(raises=MethodInvalid)
def test_chart_calendar_no_year_provided():
    Stats(data=[]).chart_calendar()


def test_chart_calendar(_data, _chart_calendar_expect_january_with_data):
    actual = Stats(year=1999, data=_data).chart_calendar()

    assert actual[0] == _chart_calendar_expect_january_with_data


@pytest.mark.django_db
@patch(f'project.{App_name}.models.CountQuerySet.App_name', 'Counter Type')
def test_chart_calendar_db(_chart_calendar_expect_january_with_data, _data_db):
    year = 1999
    qs = Count.objects.sum_by_day(year=year)
    actual = Stats(year=year, data=qs).chart_calendar()

    assert actual[0] == _chart_calendar_expect_january_with_data


def test_chart_calendar_no_data(_data, _chart_calendar_expect_january_no_data):
    actual = Stats(year=1999, data=[]).chart_calendar()

    assert actual[0] == _chart_calendar_expect_january_no_data


@freeze_time('1999-01-02')
def test_chart_calendar_current_day_no_data(_chart_calendar_expect_january_no_data):
    _chart_calendar_expect_january_no_data['data'][5][2] = 0.05

    actual = Stats(year=1999, data=[]).chart_calendar()

    assert actual[0] == _chart_calendar_expect_january_no_data


@freeze_time('1999-01-01')
def test_chart_calendar_first_day_of_year_with_record(_chart_calendar_expect_january_no_data):
    _data = [{'date': date(1999, 1, 1), 'qty': 1.0},]

    _chart_calendar_expect_january_no_data['data'][4].append(1.0) #1999-01-08 qty
    _chart_calendar_expect_january_no_data['data'][4].append(0) #1999-01-08 gap
    _chart_calendar_expect_january_no_data['data'][4][2] = 1.0

    actual = Stats(year=1999, data=_data).chart_calendar()

    assert actual[0] == _chart_calendar_expect_january_no_data
