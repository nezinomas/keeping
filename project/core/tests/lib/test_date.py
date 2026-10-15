from datetime import date, datetime, timedelta

import pytest
import pytz
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib import date as lib_date


def test_year_month_list():
    actual = lib_date.year_month_list(1970)

    assert len(actual) == 12
    assert actual[0] == date(1970, 1, 1)
    assert actual[11] == date(1970, 12, 1)


DATES = st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))


@given(today=DATES, other=DATES, same_month=st.booleans(), past=st.booleans())
@example(date(1970, 1, 11), date(1970, 1, 1), True, True)
@example(date(1970, 1, 11), date(1970, 12, 1), False, True)
@example(date(1970, 1, 11), date(2020, 2, 1), False, True)
@example(date(1970, 1, 11), date(1970, 1, 1), True, False)
@example(date(1970, 1, 11), date(1970, 12, 1), False, False)
@example(date(1970, 1, 11), date(2020, 2, 1), False, False)
def test_current_day(today, other, same_month, past):
    shown = today if same_month else other
    month_end = date(shown.year + shown.month // 12, shown.month % 12 + 1, 1)

    actual = lib_date.current_day(shown.year, shown.month, today, past)

    expect = 0
    if past:
        expect = (month_end - timedelta(days=1)).day
    if (shown.year, shown.month) == (today.year, today.month):
        expect = today.day
    assert actual == expect


@pytest.mark.parametrize(
    "year, month, with_past_day, without",
    [(1970, 1, 11, 11), (1970, 12, 31, 0), (2020, 2, 29, 0)],
)
def test_current_day_literals(year, month, with_past_day, without):
    today = date(1970, 1, 11)

    assert lib_date.current_day(year, month, today, True) == with_past_day
    assert lib_date.current_day(year, month, today, False) == without


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
