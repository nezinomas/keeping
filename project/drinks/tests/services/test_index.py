from datetime import date
from types import SimpleNamespace

import pytest
import time_machine

from project.drinks.lib.drinks_stats import DrinkStats

from ...lib.drinks_options import DrinkConverter
from ...services.index.builders import (
    ConversionRowViewModel,
    DryDaysViewModel,
    IndexBuilder,
)
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="drink_converter")
def fixture_drink_converter():
    return DrinkConverter("beer")


@pytest.mark.parametrize(
    "past, current, expect",
    [
        (date(1998, 1, 1), None, DryDaysViewModel(date(1998, 1, 1), 367)),
        (None, date(1999, 1, 1), DryDaysViewModel(date(1999, 1, 1), 2)),
        (date(1998, 1, 1), date(1999, 1, 1), DryDaysViewModel(date(1999, 1, 1), 2)),
        (None, None, DryDaysViewModel(None, 0)),
    ],
)
@time_machine.travel("1999-01-03")
def test_dry_days(past, current, expect, main_user, drink_converter):
    DrinkFactory()

    actual = IndexBuilder(
        converter=drink_converter,
        drink_stats=DrinkStats(drink_converter),
        latest_past_date=past,
        latest_current_date=current,
    ).tbl_dry_days()

    assert actual == expect


def test_dry_days_no_records(main_user, drink_converter):
    actual = IndexBuilder(
        converter=drink_converter, drink_stats=DrinkStats(drink_converter)
    ).tbl_dry_days()

    assert actual == DryDaysViewModel(date=None, delta=0)


@time_machine.travel("2019-10-10")
def test_std_av(main_user, drink_converter):
    actual = IndexBuilder(
        converter=drink_converter, drink_stats=DrinkStats(drink_converter)
    )._build_conversion_rows(2019, 273.5)

    assert len(actual) == 4

    assert actual[0].title == "Alus, 0.5L"
    assert round(actual[0].total, 2) == 273.5
    assert round(actual[0].per_day, 2) == 0.97
    assert round(actual[0].per_week, 2) == 6.67
    assert round(actual[0].per_month, 2) == 27.35

    assert actual[1].title == "Vynas, 0.75L"
    assert round(actual[1].total, 2) == 85.47
    assert round(actual[1].per_day, 2) == 0.3
    assert round(actual[1].per_week, 2) == 2.08
    assert round(actual[1].per_month, 2) == 8.55

    assert actual[2].title == "Degtinė, 1L"
    assert round(actual[2].total, 2) == 17.09
    assert round(actual[2].per_day, 2) == 0.06
    assert round(actual[2].per_week, 2) == 0.42
    assert round(actual[2].per_month, 2) == 1.71

    assert actual[3].title == "Std Av"
    assert round(actual[3].total, 2) == 683.75
    assert round(actual[3].per_day, 2) == 2.42
    assert round(actual[3].per_week, 2) == 16.68
    assert round(actual[3].per_month, 2) == 68.38


@time_machine.travel("2019-10-10")
def test_std_av_past_recods(main_user, drink_converter):
    actual = IndexBuilder(
        converter=drink_converter, drink_stats=DrinkStats(drink_converter)
    )._build_conversion_rows(1999, 273.5)

    assert len(actual) == 4

    assert actual[0].title == "Alus, 0.5L"
    assert round(actual[0].total, 2) == 273.5
    assert round(actual[0].per_day, 2) == 0.75
    assert round(actual[0].per_week, 2) == 5.26
    assert round(actual[0].per_month, 2) == 22.79

    assert actual[1].title == "Vynas, 0.75L"
    assert round(actual[1].total, 2) == 85.47
    assert round(actual[1].per_day, 2) == 0.23
    assert round(actual[1].per_week, 2) == 1.64
    assert round(actual[1].per_month, 2) == 7.12

    assert actual[2].title == "Degtinė, 1L"
    assert round(actual[2].total, 2) == 17.09
    assert round(actual[2].per_day, 2) == 0.05
    assert round(actual[2].per_week, 2) == 0.33
    assert round(actual[2].per_month, 2) == 1.42

    assert actual[3].title == "Std Av"
    assert round(actual[3].total, 2) == 683.75
    assert round(actual[3].per_day, 2) == 1.87
    assert round(actual[3].per_week, 2) == 13.15
    assert round(actual[3].per_month, 2) == 56.98


@pytest.mark.parametrize(
    "drink_type, qty, expect",
    [
        ("beer", 4, 0.1),
        ("wine", 1.25, 0.1),
        ("vodka", 0.25, 0.1),
        ("stdav", 10, 0.1),
    ],
)
def test_tbl_alcohol(drink_type, qty, expect, main_user, drink_converter):
    main_user.drink_type = drink_type

    stats = SimpleNamespace(
        year=1999,
        yearly=SimpleNamespace(
            total_quantity=qty,
            avg_daily_volume_ml
            =0.0,
        ),
    )

    actual = IndexBuilder(
        converter=DrinkConverter(drink_type), drink_stats=stats
    ).tbl_alcohol()

    assert actual.liters == expect


def test_dry_days_view_model_has_data():
    model_with_data = DryDaysViewModel(date=date(2026, 5, 8), delta=10)
    assert model_with_data.has_data is True

    empty_model = DryDaysViewModel()
    assert empty_model.has_data is False
