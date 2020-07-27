import calendar
from datetime import date

import pytest

from ..lib.stats import Stats


@pytest.fixture()
def _data():
    df = [
        {'date': date(1999, 1, 8), 'qty': 1.0},
        {'date': date(1999, 1, 15), 'qty': 2.0},
        {'date': date(1999, 2, 1), 'qty': 2.0},
        {'date': date(1999, 12, 3), 'qty': 1.0},
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
    actual = Stats(_data).weekdays_stats()

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


def test_weekdays_stats_no_data():
    actual = Stats([]).weekdays_stats()

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
    actual = Stats(_data).months_stats()

    expect = [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    assert actual == expect


def test_months_stats_no_data():
    actual = Stats([]).months_stats()

    expect = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    assert actual == expect


def test_year_stats(_data, _year_stats_expect):
    actual = Stats(_data).year_stats(1999)

    assert actual == _year_stats_expect


def test_year_stats_no_data(_year_stats_expect_empty):
    actual = Stats([]).year_stats(1999)

    assert actual == _year_stats_expect_empty


def test_year_stats_months_len():
    actual = Stats([]).year_stats(1999)

    assert len(actual[0]) == 31  # sausis
    assert len(actual[1]) == 28  # vasaris
    assert len(actual[2]) == 31  # kovas
    assert len(actual[3]) == 30  # balandis
    assert len(actual[4]) == 31  # gegužė
    assert len(actual[5]) == 30  # birželis
    assert len(actual[6]) == 31  # liepa
    assert len(actual[7]) == 31  # rugpjūtis
    assert len(actual[8]) == 30  # rugsėjis
    assert len(actual[9]) == 31  # spalis
    assert len(actual[10]) == 30  # lapkritis
    assert len(actual[11]) == 31  # gruodis

def test_year_stats_months_len_leap_year():
    actual = Stats([]).year_stats(2000)

    assert len(actual[1]) == 29  # vasaris
