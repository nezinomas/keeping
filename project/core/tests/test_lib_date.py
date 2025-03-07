from datetime import date, datetime
from types import SimpleNamespace

import pytest
import pytz
import time_machine
from mock import patch

from ...users.factories import UserFactory
from ..lib import date as lib_date


def test_year_month_list():
    actual = lib_date.year_month_list(1970)

    assert len(actual) == 12
    assert actual[0] == date(1970, 1, 1)
    assert actual[11] == date(1970, 12, 1)


@time_machine.travel("1999-01-11")
def test_year_month_list_year_none():
    actual = lib_date.year_month_list(None)

    assert len(actual) == 12
    assert actual[0] == date(1999, 1, 1)
    assert actual[11] == date(1999, 12, 1)


@time_machine.travel("1970-01-11")
@pytest.mark.parametrize(
    "year, month, return_past_day, expect",
    [
        (1970, 1, True, 11),
        (1970, 12, True, 31),
        (2020, 2, True, 29),
        (1970, 1, False, 11),
        (1970, 12, False, None),
        (2020, 2, False, None),
    ],
)
def test_current_day(year, month, return_past_day, expect):
    assert lib_date.current_day(year, month, return_past_day) == expect


@time_machine.travel("2001-01-01")
@pytest.mark.django_db
def test_years_user_logged(main_user):
    main_user.journal.first_record = datetime(1999, 1, 1, tzinfo=pytz.utc)

    actual = lib_date.years()

    assert actual == [1999, 2000, 2001, 2002]


@pytest.mark.django_db
@time_machine.travel("2001-01-01")
@patch("project.core.lib.utils.get_user", return_value=SimpleNamespace())
def test_years_user_anonymous_user(mck):
    actual = lib_date.years()

    assert actual == [2001, 2002]


@pytest.mark.parametrize(
    "month, expect",
    [(1, "january"), (13, "january"), ("1", "january"), ("x", "january")],
)
def test_monthname(month, expect):
    assert lib_date.monthname(month) == expect


def test_monthnames():
    actual = lib_date.monthnames()

    assert len(actual) == 12
    assert actual[0] == "january"
    assert actual[1] == "february"
    assert actual[11] == "december"


def test_monthlen_leap_not():
    actual = lib_date.monthlen(1999, "february")

    assert actual == 28


def test_monthlen_leap():
    actual = lib_date.monthlen(2000, "february")

    assert actual == 29


def test_monthlen_wrong_input():
    actual = lib_date.monthlen(2, "xxx")

    assert actual == 31


@time_machine.travel("1974-01-01")
@pytest.mark.django_db
def test_set_year_for_month(main_user):
    UserFactory()

    actual = lib_date.set_year_for_form()

    assert actual == datetime(1999, 1, 1)


@time_machine.travel("2020-1-1")
@pytest.mark.parametrize(
    "year, expect", [(2020, 1), (1999, 52), (2019, 52), (2000, 53), (2003, 53)]
)
def test_weeknumber(year, expect):
    actual = lib_date.weeknumber(year=year)

    assert actual == expect


@time_machine.travel("2020-6-6")
@pytest.mark.parametrize(
    "year, expect",
    [
        (1999, (365, 365)),
        (2016, (366, 366)),
        (2020, (158, 366)),
        (None, (158, 366)),
    ],
)
def test_yday(year, expect):
    actual = lib_date.yday(year)

    assert actual == expect


@pytest.mark.parametrize("year, expect", [(2020, 366), (2019, 365)])
def test_ydays(year, expect):
    actual = lib_date.ydays(year)

    assert actual == expect
