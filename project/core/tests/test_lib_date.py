from datetime import date

import pytest
from freezegun import freeze_time
from mock import patch
from types import SimpleNamespace

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
def test_current_day():
    actual = T.current_day(1970, 1)

    assert actual == 11


@freeze_time("1970-01-11")
def test_current_day_1():
    actual = T.current_day(1970, 12)

    assert actual == 31


@freeze_time("1970-01-11")
def test_current_day_2():
    actual = T.current_day(2020, 2)

    assert actual == 29


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
