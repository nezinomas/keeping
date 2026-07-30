from datetime import date

from ...services.recent_days import RecentDaySelector


def labels(selector):
    return [label for label, _value in selector.options]


def values(selector):
    return [value for _label, value in selector.options]


def test_selected_is_the_given_day():
    assert RecentDaySelector.for_day(date(1999, 1, 15)).selected == "1999-01-15"


def test_five_days_to_choose_from():
    assert len(RecentDaySelector.for_day(date(1999, 1, 15)).options) == 5


def test_values_are_the_given_day_and_the_four_before_it():
    actual = RecentDaySelector.for_day(date(1999, 1, 15))

    assert values(actual) == [
        "1999-01-15",
        "1999-01-14",
        "1999-01-13",
        "1999-01-12",
        "1999-01-11",
    ]


def test_first_two_days_are_named_today_and_yesterday():
    actual = RecentDaySelector.for_day(date(1999, 1, 15))

    assert labels(actual)[:2] == ["Šiandien", "Vakar"]


def test_older_days_are_named_by_their_weekday():
    # 1999-01-15 is a Friday
    actual = RecentDaySelector.for_day(date(1999, 1, 15))

    assert labels(actual)[2:] == ["Trečiadienis", "Antradienis", "Pirmadienis"]


def test_older_days_can_be_weekend_days():
    # 1999-03-03 is a Wednesday, so the oldest day is a Saturday
    actual = RecentDaySelector.for_day(date(1999, 3, 3))

    assert labels(actual)[2:] == ["Pirmadienis", "Sekmadienis", "Šeštadienis"]


def test_days_reach_back_over_a_month_boundary():
    actual = RecentDaySelector.for_day(date(1999, 3, 2))

    assert values(actual) == [
        "1999-03-02",
        "1999-03-01",
        "1999-02-28",
        "1999-02-27",
        "1999-02-26",
    ]


def test_days_reach_back_over_a_year_boundary():
    actual = RecentDaySelector.for_day(date(1999, 1, 2))

    assert values(actual) == [
        "1999-01-02",
        "1999-01-01",
        "1998-12-31",
        "1998-12-30",
        "1998-12-29",
    ]


def test_options_are_a_list_not_an_iterator():
    selector = RecentDaySelector.for_day(date(1999, 1, 15))

    assert list(selector.options) == list(selector.options)


def test_needs_only_a_day():
    """No request, no user — the picker never depends on the year being browsed."""
    assert RecentDaySelector.for_day(date(1974, 1, 1)).selected == "1974-01-01"
