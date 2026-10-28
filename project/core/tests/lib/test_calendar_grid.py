from datetime import date

import pytest
from django.utils import translation
from django.utils.translation import gettext as _

from ...lib.calendar_grid import CalendarGrid
from ...lib.day_stats import NoPastRecord, PastRecord
from ...lib.year_boundary import YearBoundary

pytestmark = pytest.mark.django_db

THRESHOLDS = (2.0, 4.0, 6.0)


def test_build_empty_returns_full_year():
    grid = CalendarGrid.build(YearBoundary(1999, date(1999, 6, 15)), daily_data=[])

    assert len(grid.months) == 12
    assert all(d.level == 0 for m in grid.months for d in m.days)
    assert all(d.label == "" for m in grid.months for d in m.days if d.is_future)
    gap_str = _("Gap")
    assert grid.months[5].days[14].label == f"1999-06-15\n{gap_str}: 0d."


def test_build_month_metadata():
    grid = CalendarGrid.build(YearBoundary(1999, date(1999, 12, 31)), daily_data=[])

    jan = grid.months[0]
    assert jan.number == 1
    assert jan.name == "Sausis"
    assert len(jan.days) == 31
    assert jan.leading_blanks == date(1999, 1, 1).weekday()

    feb = grid.months[1]
    assert feb.number == 2
    assert len(feb.days) == 28
    assert feb.leading_blanks == date(1999, 2, 1).weekday()


def test_build_all_levels_and_labels():
    daily = [
        {"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4},
        {"date": date(1999, 1, 2), "stdav": 2.0, "qty": 0.8},
        {"date": date(1999, 1, 3), "stdav": 4.0, "qty": 1.6},
        {"date": date(1999, 1, 4), "stdav": 6.0, "qty": 2.4},
        {"date": date(1999, 1, 5), "stdav": 0.0, "qty": 0.0},
    ]

    days = (
        CalendarGrid.build(
            YearBoundary(1999, date(1999, 12, 31)),
            daily_data=daily,
            thresholds=THRESHOLDS,
            value_key="stdav",
            empty_title=_("No drink"),
        )
        .months[0]
        .days
    )

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert [d.level for d in days[:5]] == [1, 2, 3, 4, 0]
    assert days[0].label == f"1999-01-01\n{qty_str}: 0.4\n{gap_str}: 0d."
    assert days[3].label == f"1999-01-04\n{qty_str}: 2.4\n{gap_str}: 1d."
    assert days[4].label == f"1999-01-05\n{_('No drink')}"
    assert days[0].gap == 0
    assert days[3].gap == 1


def test_build_gaps_with_an_earlier_record():
    daily = [
        {"date": date(1999, 1, 10), "stdav": 1.0, "qty": 0.5},
        {"date": date(1999, 1, 15), "stdav": 2.0, "qty": 1.0},
    ]
    grid = CalendarGrid.build(
        YearBoundary(1999, date(1999, 12, 31)),
        daily_data=daily,
        earlier=PastRecord(date(1999, 1, 5)),
    )

    jan_days = grid.months[0].days
    day_10 = jan_days[9]
    day_15 = jan_days[14]

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert day_10.gap == 5
    assert day_10.label == f"1999-01-10\n{qty_str}: 0.5\n{gap_str}: 5d."
    assert day_15.gap == 5
    assert day_15.label == f"1999-01-15\n{qty_str}: 1.0\n{gap_str}: 5d."


def test_build_future_flags():
    grid = CalendarGrid.build(YearBoundary(1999, date(1999, 6, 15)), daily_data=[])

    june = grid.months[5].days
    assert june[14].is_future is False
    assert june[15].is_future is True
    assert all(not d.is_future for d in grid.months[0].days)


@pytest.mark.parametrize(
    "today, daily, earlier, gap",
    [
        pytest.param(
            date(1999, 6, 15),
            [{"date": date(1999, 6, 5), "stdav": 1.0, "qty": 0.5}],
            NoPastRecord(),
            10,
            id="without_record",
        ),
        pytest.param(
            date(1999, 1, 10),
            [],
            PastRecord(date(1998, 12, 1)),
            40,
            id="earlier_record",
        ),
        pytest.param(
            date(1999, 1, 10),
            [{"date": date(1999, 3, 1), "stdav": 1.0, "qty": 0.5}],
            PastRecord(date(1998, 12, 1)),
            40,
            id="only_future_records",
        ),
        pytest.param(
            date(1999, 1, 10),
            [],
            NoPastRecord(),
            0,
            id="no_record_anywhere",
        ),
    ],
)
def test_build_today_shows_its_date_and_the_gap_since_the_last_record(
    today, daily, earlier, gap
):
    grid = CalendarGrid.build(
        YearBoundary(1999, today), daily_data=daily, earlier=earlier
    )

    today_day = grid.months[today.month - 1].days[today.day - 1]
    assert today_day.is_today is True
    assert today_day.level == 0
    assert today_day.gap == gap
    assert today_day.label == f"{today.isoformat()}\n{_('Gap')}: {gap}d."


@pytest.mark.parametrize(
    "empty_title, expect",
    [
        pytest.param("No drink", "1999-01-01\nNo drink", id="with_a_word_for_empty"),
        pytest.param("", "1999-01-01", id="date_alone"),
    ],
)
def test_a_dry_day_is_labelled_rather_than_left_blank(empty_title, expect):
    grid = CalendarGrid.build(
        YearBoundary(1999, date(1999, 12, 31)), daily_data=[], empty_title=empty_title
    )

    assert grid.months[0].days[0].label == expect


def test_a_days_speech_is_its_label_on_one_line():
    daily = [{"date": date(1999, 1, 1), "stdav": 1.0, "qty": 0.4}]
    grid = CalendarGrid.build(YearBoundary(1999, date(1999, 12, 31)), daily_data=daily)

    qty_str = _("Quantity")
    gap_str = _("Gap")
    assert grid.months[0].days[0].speech == (
        f"1999-01-01, {qty_str}: 0.4, {gap_str}: 0d."
    )


@pytest.mark.parametrize(
    "thresholds, expect",
    [
        pytest.param(
            THRESHOLDS,
            ("0", "<2", "2-4", "4-6", "≥6"),
            id="every_level",
        ),
        pytest.param((), ("0", "≥1"), id="without_thresholds"),
    ],
)
def test_legend_bounds_follow_the_thresholds(thresholds, expect):
    grid = CalendarGrid.build(
        YearBoundary(1999, date(1999, 12, 31)), daily_data=[], thresholds=thresholds
    )

    assert grid.legend.bounds == expect


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"low_title": "nothing", "high_title": "plenty"}, id="end_words"),
        pytest.param({"unit": "Std Av"}, id="unit"),
    ],
)
def test_legend_carries_what_it_is_handed(kwargs):
    grid = CalendarGrid.build(
        YearBoundary(1999, date(1999, 12, 31)), daily_data=[], **kwargs
    )

    assert {name: getattr(grid.legend, name) for name in kwargs} == kwargs


def test_without_thresholds_every_day_with_a_value_is_one_level():
    daily = [
        {"date": date(1999, 1, 1), "qty": 0.1},
        {"date": date(1999, 1, 2), "qty": 99.0},
        {"date": date(1999, 1, 3), "qty": 0.0},
    ]
    grid = CalendarGrid.build(YearBoundary(1999, date(1999, 12, 31)), daily_data=daily)

    assert [d.level for d in grid.months[0].days[:3]] == [1, 1, 0]


@pytest.mark.parametrize(
    "year", [pytest.param(1998, id="other_year"), pytest.param(2000, id="not_started")]
)
def test_a_year_other_than_the_running_one_has_no_future_days(year):
    grid = CalendarGrid.build(YearBoundary(year, date(1999, 6, 15)), daily_data=[])

    assert all(not d.is_future for m in grid.months for d in m.days)


@pytest.mark.parametrize(
    "language, kwargs, expect",
    [
        pytest.param("lt", {"quantity_title": "Count"}, "Count: 5.0", id="custom"),
        pytest.param("lt", {}, "Kiekis: 5.0", id="default_lithuanian"),
        pytest.param("en", {}, "Quantity: 5.0", id="default_english"),
    ],
)
def test_the_quantity_title_is_the_one_handed_or_the_active_languages(
    language, kwargs, expect
):
    daily = [{"date": date(1999, 1, 1), "qty": 5.0}]
    boundary = YearBoundary(1999, date(1999, 12, 31))

    with translation.override(language):
        label = CalendarGrid.build(boundary, daily, **kwargs).months[0].days[0].label

    assert expect in label
