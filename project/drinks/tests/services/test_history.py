from datetime import date

import pytest
from django.utils.translation import gettext as _

from ...services import history
from ..factories import DrinkFactory


@pytest.mark.parametrize(
    "year, record_year, expect",
    [
        pytest.param(1999, 1998, [1998, 1999, 2000], id="run_to_the_calendar_year"),
        # a Selected year ahead of the calendar year still gets its column
        pytest.param(2001, 1999, [1999, 2000, 2001], id="reach_the_selected_year"),
    ],
)
def test_years(year, record_year, expect):
    qs = [{"year": record_year, "qty": 1, "stdav": 2.5}]
    actual = history.HistoryService(year, "beer", qs, date(2000, 1, 1)).years

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 1, 2.5, [0.025, 0.0]),
        ("wine", 1, 8, [0.08, 0.0]),
        ("vodka", 1, 40, [0.4, 0.0]),
        ("stdav", 1, 10, [0.1, 0.0]),
    ],
)
def test_pure_alcohol(drink_type, qty, stdav, expect):
    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(1999, drink_type, qs, date(2000, 1, 1)).alcohol

    assert actual == expect


@pytest.mark.django_db
@pytest.mark.parametrize(
    "drink_type, unit, decimals",
    [
        ("beer", "ml", 0),
        ("wine", "ml", 0),
        ("vodka", "ml", 0),
        ("stdav", "Std Av", 1),
    ],
)
def test_chart_is_labelled_in_the_selected_unit(drink_type, unit, decimals, main_user):
    """A Std Av day is shown as typed, so the chart cannot claim millilitres."""
    chart = history.load_service(main_user, 1999, drink_type, date(2000, 1, 1))["chart"]

    assert chart["unit"] == unit
    assert chart["decimals"] == decimals
    assert chart["text"]["per_day"] == f"{_('Average per day')}, {unit}"


@pytest.mark.parametrize(
    "drink_type, years, qty, stdav, expect",
    [
        ("beer", [1999], 365, 912.5, [500.0, 0.0]),
        ("wine", [1999], 365, 2_920, [750.0, 0.0]),
        ("vodka", [1999], 365, 14_600, [1000.0, 0.0]),
        # 365 Std Av over 365 days is 1 a day — not the 10 ml of alcohol in it
        ("stdav", [1999], 365, 365, [1.0, 0.0]),
        # a finished leap year divides by its 366 days
        ("stdav", [1996], 366, 366, [1.0, 0.0, 0.0, 0.0, 0.0]),
        # the running year 2000 has reached one day, its whole total
        ("beer", [1999, 2000], 365, 912.5, [500.0, 182_500]),
        ("wine", [1999, 2000], 365, 2_920, [750.0, 273_750]),
        ("vodka", [1999, 2000], 365, 14_600, [1000.0, 365_000]),
        ("stdav", [1999, 2000], 365, 365, [1.0, 365]),
    ],
)
def test_per_day(drink_type, years, qty, stdav, expect):
    qs = [{"year": year, "qty": qty, "stdav": stdav} for year in years]

    actual = history.HistoryService(1999, drink_type, qs, date(2000, 1, 1)).per_day

    assert actual == expect


@pytest.mark.parametrize(
    "drink_type, qty, stdav, expect",
    [
        ("beer", 365, 912.5, [365.0, 0.0]),
        ("wine", 365, 2_920, [365.0, 0.0]),
        ("vodka", 365, 14_600, [365.0, 0.0]),
        ("stdav", 365, 365, [365.0, 0.0]),
    ],
)
def test_quantity(drink_type, qty, stdav, expect):
    qs = [{"year": 1999, "qty": qty, "stdav": stdav}]

    actual = history.HistoryService(1999, drink_type, qs, date(2000, 1, 1)).quantity

    assert actual == expect


def test_a_record_in_the_selected_year_is_not_dropped():
    qs = [{"year": 2001, "qty": 1, "stdav": 2.5}]
    service = history.HistoryService(2001, "beer", qs, date(2000, 1, 1))

    assert service.years == [2001]
    assert service.quantity == [1.0]


@pytest.mark.parametrize(
    "year, qs, expect",
    [
        # day 100 of a non-leap year: 100 L so far / 100 days * 365 days = 365 L
        pytest.param(
            1999,
            [{"year": 2001, "qty": 1, "stdav": 10_000}],
            [{"x": 0, "y": pytest.approx(365.0)}],
            id="for_the_running_year",
        ),
        # only 1999 has data; the implicit 2001 column still gets its own point
        pytest.param(
            1999,
            [{"year": 1999, "qty": 1, "stdav": 25}],
            [{"x": 2, "y": 0.0}],
            id="only_the_calendar_year_carries_one",
        ),
        pytest.param(
            2002,
            [{"year": 2001, "qty": 1, "stdav": 10_000}],
            [{"x": 0, "y": pytest.approx(365.0)}],
            id="follows_the_calendar_year_not_the_selected_year",
        ),
        pytest.param(1999, [], [], id="empty_with_no_data"),
    ],
)
def test_forecast(year, qs, expect):
    actual = history.HistoryService(year, "beer", qs, date(2001, 4, 10)).forecast

    assert actual == expect


def test_forecast_does_not_follow_drink_type():
    """The bottom pane is pure alcohol, and never follows the Drink type switcher."""
    qs = [{"year": 2001, "qty": 1, "stdav": 10_000}]

    stdav_service = history.HistoryService(1999, "stdav", qs, date(2001, 4, 10))
    beer_service = history.HistoryService(1999, "beer", qs, date(2001, 4, 10))

    assert stdav_service.forecast == beer_service.forecast
    assert stdav_service.alcohol == beer_service.alcohol


@pytest.mark.django_db
def test_chart_carries_forecast_and_its_text(main_user):
    chart = history.load_service(main_user, 1999, "beer", date(2000, 1, 1))["chart"]

    assert chart["forecast"] == []
    assert chart["text"]["forecast"] == _("Forecast")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "today, records",
    [
        pytest.param(date(1999, 6, 1), 0, id="one_year_draws_no_chart"),
        pytest.param(date(2000, 6, 1), 2, id="two_years_draw_it"),
    ],
)
def test_records_count_two_years_or_none(today, records, main_user):
    DrinkFactory(date=date(1999, 1, 1))

    assert history.load_service(main_user, 1999, "beer", today)["records"] == records


@pytest.mark.django_db
def test_the_running_year_stops_at_today_and_a_coming_year_keeps_its_drinks(main_user):
    DrinkFactory(date=date(1999, 3, 1), stdav=2.5)
    DrinkFactory(date=date(1999, 4, 10), stdav=2.5)
    DrinkFactory(date=date(2000, 2, 1), stdav=10)

    chart = history.load_service(main_user, 2000, "stdav", date(1999, 3, 1))["chart"]

    assert chart["data_alcohol"] == [0.025, 0.1]


def test_a_coming_years_per_day_is_a_gap_and_its_total_stays():
    """Day 166 of 2026; 2027 has reached no day, so its average is Highcharts' gap."""
    qs = [
        {"year": 2026, "qty": 1, "stdav": 166},
        {"year": 2027, "qty": 1, "stdav": 10},
    ]
    service = history.HistoryService(2027, "stdav", qs, date(2026, 6, 15))

    assert (service.per_day, service.alcohol[1]) == ([1.0, None], 0.1)
