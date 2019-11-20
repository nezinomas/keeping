from datetime import date
from types import SimpleNamespace

import pytest
from freezegun import freeze_time
from mock import patch

from ..lib import date as T


def test_year_month_list():
    actual = T.year_month_list(1970)

    assert len(actual) == 12
    assert actual[0] == date(1970, 1, 1)
    assert actual[11] == date(1970, 12, 1)


@freeze_time("1999-01-11")
def test_year_month_list_year_none():
    actual = T.year_month_list(None)

    assert len(actual) == 12
    assert actual[0] == date(1999, 1, 1)
    assert actual[11] == date(1999, 12, 1)


@freeze_time("1970-01-11")
@pytest.mark.parametrize(
    'year, month, expect',
    [
        (1970, 1, 11),
        (1970, 12, 31),
        (2020, 2, 29),
    ]
)
def test_current_day(year, month, expect):
    assert T.current_day(year, month) == expect


@freeze_time("2001-01-01")
@pytest.mark.django_db
def test_years_user_logged(get_user):
    get_user.date_joined = date(1999, 1, 1)

    actual = T.years()

    assert actual == [1999, 2000, 2001, 2002]


@pytest.mark.django_db
@freeze_time("2001-01-01")
@patch('project.core.lib.utils.get_user', return_value=SimpleNamespace())
def test_years_user_anonymous_user(mck):
    actual = T.years()

    assert actual == [2001, 2002]


def test_monthname_correct():
    assert T.monthname(1) == 'january'


def test_monthname_wrong_number():
    assert T.monthname(13) == 'january'


def test_monthnames():
    actual = T.monthnames()

    assert len(actual) == 12
    assert actual[0] == 'january'
    assert actual[1] == 'february'
    assert actual[11] == 'december'


def test_monthlen_leap_not():
    actual = T.monthlen(1999, 'february')

    assert actual == 28


def test_monthlen_leap():
    actual = T.monthlen(2000, 'february')

    assert actual == 29


def test_monthlen_wrong_input():
    actual = T.monthlen(2, 'xxx')

    assert actual == 31
