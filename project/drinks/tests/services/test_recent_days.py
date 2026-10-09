from datetime import date

import pytest

from ...services.recent_days import RecentDaySelector


def labels(selector):
    return [label for label, _value in selector.options]


def values(selector):
    return [value for _label, value in selector.options]


@pytest.mark.parametrize(
    "day, expected",
    [
        pytest.param(date(1999, 1, 15), "1999-01-15", id="selected_is_the_given_day"),
        pytest.param(date(1974, 1, 1), "1974-01-01", id="needs_only_a_day"),
    ],
)
def test_selected_is_the_given_day_in_iso_form(day, expected):
    assert RecentDaySelector.for_day(day).selected == expected


def test_five_days_to_choose_from():
    assert len(RecentDaySelector.for_day(date(1999, 1, 15)).options) == 5


@pytest.mark.parametrize(
    "day, expected",
    [
        pytest.param(
            date(1999, 1, 15),
            ["1999-01-15", "1999-01-14", "1999-01-13", "1999-01-12", "1999-01-11"],
            id="values_are_the_given_day_and_the_four_before_it",
        ),
        pytest.param(
            date(1999, 3, 2),
            ["1999-03-02", "1999-03-01", "1999-02-28", "1999-02-27", "1999-02-26"],
            id="days_reach_back_over_a_month_boundary",
        ),
        pytest.param(
            date(1999, 1, 2),
            ["1999-01-02", "1999-01-01", "1998-12-31", "1998-12-30", "1998-12-29"],
            id="days_reach_back_over_a_year_boundary",
        ),
    ],
)
def test_values_reach_back_four_days_from_the_given_day(day, expected):
    assert values(RecentDaySelector.for_day(day)) == expected


def test_first_two_days_are_named_today_and_yesterday():
    actual = RecentDaySelector.for_day(date(1999, 1, 15))

    assert labels(actual)[:2] == ["Šiandien", "Vakar"]


@pytest.mark.parametrize(
    "day, expect",
    [
        pytest.param(
            date(1999, 1, 15),
            ["Trečiadienis", "Antradienis", "Pirmadienis"],
            id="friday",
        ),
        pytest.param(
            date(1999, 3, 3),
            ["Pirmadienis", "Sekmadienis", "Šeštadienis"],
            id="wednesday_reaches_a_weekend",
        ),
    ],
)
def test_older_days_are_named_by_their_weekday(day, expect):
    actual = RecentDaySelector.for_day(day)

    assert labels(actual)[2:] == expect


def test_options_are_a_list_not_an_iterator():
    selector = RecentDaySelector.for_day(date(1999, 1, 15))

    assert list(selector.options) == list(selector.options)
