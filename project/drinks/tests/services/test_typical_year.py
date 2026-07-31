from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ...lib.drinks_risk import HEAVY_DAY_STDAV
from ...services.typical_year import (
    MonthTotal,
    TypicalYear,
    TypicalYearBuilder,
    TypicalYearChartViewModel,
    TypicalYearProfile,
)
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


def _total(year: int, month: int, stdav: float, drinking_days: int) -> MonthTotal:
    return MonthTotal(year=year, month=month, stdav=stdav, drinking_days=drinking_days)


def _profile(rows=(), today=date(2022, 6, 1)) -> TypicalYearProfile:
    return TypicalYearProfile.pool(rows, today=today)


# -------------------------------------------------------------------------------------
#                                                             TypicalYearProfile.pool
# -------------------------------------------------------------------------------------
def test_pool_is_always_twelve_months_january_first():
    actual = _profile([_total(2020, 5, 10, 1)])

    assert [point.month for point in actual.points] == list(range(1, 13))


def test_pool_two_years_of_identical_shape_pool_to_that_shape():
    one_year = _profile([_total(2020, 1, 40, 4)])
    two_years = _profile([_total(2020, 1, 40, 4), _total(2021, 1, 40, 4)])

    assert (
        two_years.points[0].drinking_day_share == one_year.points[0].drinking_day_share
    )
    assert two_years.points[0].intensity == one_year.points[0].intensity


def test_pool_sums_both_halves_of_every_month():
    actual = _profile([_total(2020, 1, 40, 4), _total(2021, 1, 20, 2)])

    assert actual.points[0].stdav == 60
    assert actual.points[0].drinking_days == 6
    assert actual.points[0].calendar_days == 62  # two Januaries
    assert actual.points[0].intensity == 10


def test_pool_a_month_absent_from_one_year_still_counts_its_days():
    # 2021 was logged, so its empty January is a January the user did not drink
    # in — not a January that is missing from the denominator
    actual = _profile(
        [_total(2020, 1, 20, 2), _total(2020, 2, 20, 2), _total(2021, 2, 20, 2)]
    )

    assert actual.points[0].drinking_days == 2
    assert actual.points[0].calendar_days == 62
    assert actual.points[1].drinking_days == 4
    assert actual.points[1].calendar_days == 57  # 29 in 2020, 28 in 2021


def test_pool_a_year_with_no_records_contributes_no_days():
    # the pooled range may span a year the user never logged; counting its days
    # as dry would push every rate down for a year nobody was recording
    actual = _profile([_total(2020, 1, 20, 2), _total(2022, 1, 20, 2)])

    assert actual.points[0].calendar_days == 62


def test_pool_the_running_year_stops_at_today():
    actual = _profile([_total(2026, 7, 30, 3)], today=date(2026, 7, 15))

    assert actual.points[6].calendar_days == 15
    assert actual.points[6].drinking_day_share == 0.2
    assert actual.points[7].calendar_days == 0


def test_pool_mixes_a_finished_year_with_the_running_one():
    actual = _profile(
        [_total(2025, 7, 30, 3), _total(2026, 7, 30, 3)], today=date(2026, 7, 15)
    )

    assert actual.points[6].calendar_days == 46  # all of 2025-07, half of 2026-07


def test_pool_a_month_with_no_records_is_zero_not_a_division_error():
    actual = _profile([_total(2020, 1, 40, 4)])

    assert actual.points[1].drinking_days == 0
    assert actual.points[1].drinking_day_share == 0.0
    assert actual.points[1].intensity == 0.0
    assert actual.points[1].calendar_days == 29


def test_pool_span_is_the_first_and_last_year_with_records():
    actual = _profile(
        [_total(2020, 1, 10, 1), _total(2015, 5, 10, 1), _total(2025, 9, 10, 1)]
    )

    assert actual.year_from == 2015
    assert actual.year_to == 2025
    assert actual.has_data


def test_pool_without_rows_has_no_data():
    actual = _profile()

    assert not actual.has_data
    assert len(actual.points) == 12
    assert actual.points[0].calendar_days == 0
    assert actual.points[0].drinking_day_share == 0.0


@time_machine.travel("2026-07-15")
def test_pool_today_defaults_to_the_day_it_runs_on():
    actual = TypicalYearProfile.pool([_total(2026, 7, 30, 3)])

    assert actual.points[6].calendar_days == 15


# -------------------------------------------------------------------------------------
#                                                              TypicalYearBuilder.chart
# -------------------------------------------------------------------------------------
def test_chart_view_model():
    actual = TypicalYearBuilder(_profile([_total(2020, 1, 40, 4)])).chart()

    assert isinstance(actual, TypicalYearChartViewModel)
    assert len(actual.categories) == 12
    assert len(actual.drinking_day_share) == 12
    assert len(actual.intensity) == 12
    assert actual.heavy_threshold == HEAVY_DAY_STDAV


def test_chart_categories_are_the_month_names_january_first():
    actual = TypicalYearBuilder(_profile()).chart()

    assert actual.categories[0] == _("January")
    assert actual.categories[11] == _("December")


def test_chart_rate_is_a_percentage():
    # 3 of the 15 days July has reached, so 20.0 rather than 0.2
    actual = TypicalYearBuilder(
        _profile([_total(2026, 7, 30, 3)], today=date(2026, 7, 15))
    ).chart()

    assert actual.drinking_day_share[6] == 20.0


def test_chart_intensity_carries_the_std_av_unit_and_one_decimal():
    # 33.7 Std Av over 3 drinking days is 11.2333: a Std Av rounded to whole is
    # destroyed, and the axis is Std Av whatever the drink-type dropdown says
    actual = TypicalYearBuilder(_profile([_total(2020, 8, 33.7, 3)])).chart()

    assert actual.intensity[7] == 11.2
    assert actual.text["intensity_unit"] == "Std Av"
    assert actual.text["share_unit"] == "%"


def test_chart_names_the_pooled_range():
    profile = _profile([_total(2015, 1, 10, 1), _total(2025, 1, 10, 1)])

    actual = TypicalYearBuilder(profile).chart()

    assert actual.year_from == 2015
    assert actual.year_to == 2025
    assert actual.text["subtitle"] == "Apjungti 2015–2025 m."
    assert actual.text["title"] == _("Typical year")


def test_chart_of_a_single_year_names_that_year_alone():
    actual = TypicalYearBuilder(_profile([_total(2025, 1, 10, 1)])).chart()

    assert actual.text["subtitle"] == "2025"


def test_chart_without_data_says_so_and_captions_nothing():
    actual = TypicalYearBuilder(_profile()).chart()

    assert not actual.has_data
    assert actual.text["subtitle"] == ""


# -------------------------------------------------------------------------------------
#                                                                     TypicalYear.build
# -------------------------------------------------------------------------------------
@time_machine.travel("2026-07-15")
def test_build_pools_the_full_span_by_default(main_user):
    DrinkFactory(date=date(2015, 1, 5), stdav=5)
    DrinkFactory(date=date(2025, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user)

    assert actual.year_from == 2015
    assert actual.year_to == 2025


@time_machine.travel("2026-07-15")
def test_build_pools_only_the_selected_years(main_user):
    DrinkFactory(date=date(2015, 1, 5), stdav=5)
    DrinkFactory(date=date(2020, 1, 5), stdav=5)
    DrinkFactory(date=date(2025, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user, 2020, 2025)

    assert actual.year_from == 2020
    assert actual.year_to == 2025
    # two Januaries pooled, not three
    assert actual.drinking_day_share[0] == round(2 / 62 * 100, 1)


@time_machine.travel("2026-07-15")
def test_build_counts_drinking_days_not_rows(main_user):
    DrinkFactory(date=date(2020, 1, 5), stdav=5)
    DrinkFactory(date=date(2020, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user)

    assert actual.drinking_day_share[0] == round(1 / 31 * 100, 1)
    assert actual.intensity[0] == 10.0


@pytest.mark.parametrize("years", [1, 5])
def test_build_is_one_query_however_many_years(
    main_user, years, django_assert_num_queries
):
    for year in range(2020, 2020 + years):
        DrinkFactory(date=date(year, 3, 5), stdav=5)

    with django_assert_num_queries(1):
        TypicalYear.build(main_user)


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
@time_machine.travel("2026-07-15")
def test_build_is_the_same_chart_under_every_drink_type(drink_type, main_user):
    # both series are unit-free or Std Av, so the drink-type dropdown must not
    # reach this chart at all
    main_user.drink_type = drink_type
    DrinkFactory(date=date(2020, 8, 5), stdav=11.2)

    actual = TypicalYear.build(main_user)

    assert actual.intensity[7] == 11.2
    assert actual.drinking_day_share[7] == round(1 / 31 * 100, 1)


def test_build_without_records_has_no_data(main_user):
    actual = TypicalYear.build(main_user)

    assert not actual.has_data
    assert actual.year_from == 0
