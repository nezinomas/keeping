from datetime import date, datetime

import pytest
import pytz

from ...lib import date as lib_date


def test_year_month_list():
    actual = lib_date.year_month_list(1970)

    assert len(actual) == 12
    assert actual[0] == date(1970, 1, 1)
    assert actual[11] == date(1970, 12, 1)


@pytest.mark.parametrize(
    "year, month, return_past_day, expect",
    [
        (1970, 1, True, 11),
        (1970, 12, True, 31),
        (2020, 2, True, 29),
        (1970, 1, False, 11),
        (1970, 12, False, 0),
        (2020, 2, False, 0),
    ],
)
def test_current_day(year, month, return_past_day, expect):
    actual = lib_date.current_day(year, month, date(1970, 1, 11), return_past_day)

    assert actual == expect


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("years_of", "expected"),
    [
        (lib_date.years, [1999, 2000, 2001, 2002]),
        (lib_date.years_to_date, [1999, 2000, 2001]),
    ],
    ids=["years", "years_to_date"],
)
def test_years_user_logged(main_user, years_of, expected):
    main_user.journal.first_record = datetime(1999, 1, 1, tzinfo=pytz.utc)

    actual = years_of(main_user, date(2001, 1, 1))

    assert actual == expected


def test_monthnames():
    actual = lib_date.monthnames()

    assert len(actual) == 12
    assert actual[0] == "january"
    assert actual[1] == "february"
    assert actual[11] == "december"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param(date(1974, 1, 1), datetime(1999, 1, 1), id="same_day"),
        pytest.param(
            date(2028, 2, 29), datetime(1999, 2, 28), id="leap_day_in_common_year"
        ),
    ],
)
def test_set_year_for_month(main_user, today, expect):
    actual = lib_date.set_date_with_user_year(main_user, today)

    assert actual == expect


@pytest.mark.parametrize(
    "year, expect",
    [
        (1999, (365, 365)),
        (2016, (366, 366)),
        (2020, (158, 366)),
        (2021, (0, 365)),
    ],
)
def test_yday(year, expect):
    actual = lib_date.yday(year, date(2020, 6, 6))

    assert actual == expect


@pytest.mark.parametrize("year, expect", [(2020, 366), (2019, 365)])
def test_ydays(year, expect):
    actual = lib_date.ydays(year)

    assert actual == expect
