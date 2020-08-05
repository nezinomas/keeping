import calendar
from datetime import date

import pytest
from mock import patch

from ...core.exceptions import MethodInvalid
from ..factories import NightFactory
from ..lib.stats import Stats
from ..models import Night

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
@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_year_totals_queryset(get_user):
    NightFactory()
    qs = Night.objects.year(1999)

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
@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_items(get_user):
    NightFactory()
    qs = Night.objects.year(1999)

    actual = Stats(year=1999, data=qs).items()

    assert len(actual) == 1

    actual = actual[0]

    assert actual['quantity'] == 1
    assert actual['date'] == date(1999, 1, 1)


@pytest.mark.django_db
@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_items_odering(get_user):
    NightFactory(date=date(1999, 1, 1))
    NightFactory(date=date(1999, 12, 31))

    qs = Night.objects.year(1999)

    actual = Stats(year=1999, data=qs).items()

    assert actual[0]['date'] == date(1999, 12, 31)
    assert actual[1]['date'] == date(1999, 1, 1)


@pytest.mark.django_db
@patch('project.nights.models.NightQuerySet.App_name', 'Counter Type')
def test_items_no_data(get_user):
    qs = Night.objects.year(1999)

    actual = Stats(year=1999, data=qs).items()

    assert actual == []


def test_gaps_for_current_year(_data):
    actual = Stats(year=1999, data=_data).gaps()

    assert actual == [7, 7, 17, 305]


def test_gaps_for_all_years(_data):
    actual = Stats(data=_data).gaps()

    assert actual == [7, 7, 17, 305, 36]


def test_pats_no_data():
    actual = Stats(year=1999, data=[]).gaps()

    assert actual == []
