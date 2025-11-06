from datetime import date

import pytest
import time_machine

from ..context import context_months, yday, years

pytestmark = pytest.mark.django_db


@time_machine.travel("2006-01-01")
def test_years(main_user, rf):
    expect = {"years": [2007, 2006, 2005]}

    main_user.journal.first_record = date(2005, 2, 3)
    rf.user = main_user

    actual = years(rf)

    assert len(actual["years"]) == 3
    assert expect == actual


@time_machine.travel("2006-01-01")
def test_year_first_record_from_journal(main_user, rf):
    main_user.journal.first_record = date(2004, 2, 3)

    rf.user = main_user

    actual = years(rf)
    expect = [2007, 2006, 2005, 2004]

    assert expect == actual["years"]


@time_machine.travel("2020-6-6")
@pytest.mark.parametrize(
    "year, expect",
    [
        (1999, {"yday": 365, "ydays": 365}),
        (2016, {"yday": 366, "ydays": 366}),
        (2020, {"yday": 158, "ydays": 366}),
    ],
)
def test_yday(main_user, year, expect, rf):
    main_user.year = year
    rf.user = main_user

    actual = yday(rf.user)

    assert actual == expect


@time_machine.travel("2020-1-1")
def test_yday_anonymous_user(rf):
    actual = yday(rf)

    assert actual == {"yday": 1, "ydays": 366}


@time_machine.travel("1974-1-1")
def test_context_months(rf):
    actual = context_months(rf)

    assert len(actual["context_months"]) == 12
    assert actual["context_months"][0] == date(1974, 1, 1)
