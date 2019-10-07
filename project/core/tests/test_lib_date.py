from datetime import date, datetime

import pytest
from freezegun import freeze_time

from ..lib.date import *


def test_year_month_list():
    actual = year_month_list(1970)

    assert len(actual) == 12
    assert actual[0] == date(1970, 1, 1)
    assert actual[11] == date(1970, 12, 1)


@freeze_time("1999-01-11")
def test_year_month_list_year_none():
    actual = year_month_list(None)

    assert len(actual) == 12
    assert actual[0] == date(1999, 1, 1)
    assert actual[11] == date(1999, 12, 1)


@freeze_time("1970-01-11")
def test_current_day():
    actual = current_day(1970, 1)

    assert actual == 11


@freeze_time("1970-01-11")
def test_current_day():
    actual = current_day(1970, 12)

    assert actual == 31


@freeze_time("1970-01-11")
def test_current_day():
    actual = current_day(2020, 2)

    assert actual == 29
