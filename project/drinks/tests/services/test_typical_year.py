from datetime import date

import pytest
import time_machine
from django.utils.translation import gettext as _

from ...lib.drinks_risk import HEAVY_DAY_STDAV
from ...services.typical_year import (
    MonthTotal,
    PooledRange,
    TypicalYear,
    TypicalYearBuilder,
    TypicalYearProfile,
)
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


def _total(year: int, month: int, stdav: float, drinking_days: int) -> MonthTotal:
    return MonthTotal(year=year, month=month, stdav=stdav, drinking_days=drinking_days)


def _profile(rows=(), today=date(2022, 6, 1)) -> TypicalYearProfile:
    return TypicalYearProfile.pool(rows, today=today)


def _chart(year_rows=(), pooled_rows=(), today=date(2022, 6, 1)):
    return TypicalYearBuilder(
        year=_profile(year_rows, today), pooled=_profile(pooled_rows, today)
    ).chart()


# TypicalYearProfile.pool
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


# TypicalYearBuilder.chart
def test_chart_categories_are_the_month_names_january_first():
    actual = _chart()

    assert len(actual.categories) == 12
    assert actual.categories[0] == _("January")
    assert actual.categories[11] == _("December")


def test_chart_rate_is_a_percentage():
    # 3 of the 15 days July has reached, so 20.0 rather than 0.2
    actual = _chart(year_rows=[_total(2026, 7, 30, 3)], today=date(2026, 7, 15))

    assert actual.year.drinking_day_share[6] == 20.0


def test_chart_intensity_carries_the_std_av_unit_and_one_decimal():
    # 33.7 Std Av over 3 drinking days is 11.2333: a Std Av rounded to whole is
    # destroyed, and the axis is Std Av whatever the drink-type dropdown says
    actual = _chart(year_rows=[_total(2020, 8, 33.7, 3)])

    assert actual.year.intensity[7] == 11.2
    assert actual.text["intensity_unit"] == "Std Av"
    assert actual.text["share_unit"] == "%"


@pytest.mark.parametrize(
    "year, months",
    [
        # August has not happened, so the series stops at July: plotting it as a
        # zero would draw the running year as five dry months
        pytest.param(2026, 7, id="running_year"),
        pytest.param(2025, 12, id="finished_year"),
    ],
)
def test_chart_ends_at_the_last_month_a_year_has_reached(year, months):
    actual = _chart(year_rows=[_total(year, 7, 30, 3)], today=date(2026, 7, 15))

    assert len(actual.year.drinking_day_share) == months
    assert len(actual.year.intensity) == months


def test_chart_plots_a_reached_month_without_records_as_a_zero():
    # June was lived through and no Drink was recorded: that is abstinence, and
    # it is the one thing a gap must not be confused with
    actual = _chart(year_rows=[_total(2026, 7, 30, 3)], today=date(2026, 7, 15))

    assert actual.year.drinking_day_share[5] == 0.0
    assert actual.year.intensity[5] == 0.0


@pytest.mark.parametrize(
    "year_rows, pooled_rows, year_label, pooled_label",
    [
        # the legend names each layer, because the chart plots two spans and
        # neither may be read as the other
        pytest.param(
            [],
            [_total(2015, 1, 10, 1), _total(2025, 1, 10, 1)],
            "",
            "Apjungti 2015–2025 m.",
            id="pooled_span",
        ),
        pytest.param(
            [_total(2025, 1, 10, 1)],
            [_total(2025, 1, 10, 1)],
            "2025",
            "2025",
            id="one_year_alone",
        ),
    ],
)
def test_chart_labels_each_layer_with_the_span_it_drew(
    year_rows, pooled_rows, year_label, pooled_label
):
    actual = _chart(year_rows=year_rows, pooled_rows=pooled_rows)

    assert actual.year.label == year_label
    assert actual.pooled.label == pooled_label


@pytest.mark.parametrize(
    "year_rows, pooled_rows, drawn",
    [
        pytest.param(
            [_total(2025, 1, 10, 1)],
            [_total(2015, 1, 10, 1), _total(2025, 1, 10, 1)],
            ("pooled", "year"),
            id="pooled_behind_the_year",
        ),
        pytest.param([_total(2025, 1, 10, 1)], [], ("year",), id="year_alone"),
        pytest.param(
            [],
            [_total(2015, 1, 10, 1), _total(2025, 1, 10, 1)],
            ("pooled",),
            id="pooled_alone",
        ),
        pytest.param([], [], (), id="nothing"),
    ],
)
def test_chart_draws_the_layers_that_have_data_back_to_front(
    year_rows, pooled_rows, drawn
):
    actual = _chart(year_rows=year_rows, pooled_rows=pooled_rows)
    layers = {"pooled": actual.pooled, "year": actual.year}

    assert actual.layers == [layers[name] for name in drawn]
    assert actual.has_data is bool(drawn)


def test_chart_reports_the_pooled_span_for_the_form():
    # the range boxes open on what was pooled, so the boxes and the legend agree
    actual = _chart(
        year_rows=[_total(2025, 1, 10, 1)],
        pooled_rows=[_total(2015, 1, 10, 1), _total(2025, 1, 10, 1)],
    )

    assert actual.year_from == 2015
    assert actual.year_to == 2025


def test_chart_as_dict_carries_the_layers_it_draws_and_no_python_only_span():
    actual = _chart(
        year_rows=[_total(2025, 1, 10, 1)],
        pooled_rows=[_total(2015, 1, 10, 1), _total(2025, 1, 10, 1)],
    ).as_dict

    assert sorted(actual) == ["categories", "heavy_threshold", "layers", "text"]
    assert actual["heavy_threshold"] == HEAVY_DAY_STDAV
    assert [layer["label"] for layer in actual["layers"]] == [
        "Apjungti 2015–2025 m.",
        "2025",
    ]


# PooledRange.resolve
def test_resolve_of_zero_pools_every_year_on_record():
    actual = PooledRange.resolve(2025, 0)

    # not NoPooledRange, which subclasses it
    assert type(actual) is PooledRange
    assert (actual.year_from, actual.year_to) == (0, 0)


@pytest.mark.parametrize(
    "qty, expected",
    [
        pytest.param(
            3, (2023, 2025), id="resolve_of_a_count_ends_the_span_on_the_header_year"
        ),
        pytest.param(1, (2025, 2025), id="resolve_of_one_pools_the_header_year_alone"),
    ],
)
def test_resolve_of_a_count_spans_back_from_the_header_year(qty, expected):
    actual = PooledRange.resolve(2025, qty)

    assert (actual.year_from, actual.year_to) == expected


# TypicalYear.build
@time_machine.travel("2026-07-15")
def test_build_draws_the_header_year_alone_until_a_range_is_asked_for(main_user):
    DrinkFactory(date=date(2015, 1, 5), stdav=5)
    DrinkFactory(date=date(2025, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user, 2025)

    assert actual.year.label == "2025"
    # one January, the header year's, not the two the records span
    assert actual.year.drinking_day_share[0] == round(1 / 31 * 100, 1)
    assert not actual.pooled.has_data
    assert actual.year_from == 0
    assert actual.layers == [actual.year]


@time_machine.travel("2026-07-15")
@pytest.mark.parametrize(
    "drink_years, pooled, year_from, year_to",
    [
        pytest.param(
            [2015, 2025], PooledRange(), 2015, 2025, id="every_year_on_record"
        ),
        # two Januaries pooled, not three
        pytest.param(
            [2015, 2020, 2025], PooledRange(2020, 2025), 2020, 2025, id="selected_years"
        ),
    ],
)
def test_build_pools_the_years_the_range_asks_for(
    main_user, drink_years, pooled, year_from, year_to
):
    for year in drink_years:
        DrinkFactory(date=date(year, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user, 2025, pooled)

    assert actual.year_from == year_from
    assert actual.year_to == year_to
    assert actual.pooled.drinking_day_share[0] == round(2 / 62 * 100, 1)


@time_machine.travel("2026-07-15")
def test_build_of_a_header_year_with_no_records_draws_the_pooled_layer_alone(main_user):
    DrinkFactory(date=date(2015, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user, 2025, PooledRange())

    assert not actual.year.has_data
    assert actual.layers == [actual.pooled]


@time_machine.travel("2026-07-15")
def test_build_counts_drinking_days_not_rows(main_user):
    DrinkFactory(date=date(2020, 1, 5), stdav=5)
    DrinkFactory(date=date(2020, 1, 5), stdav=5)

    actual = TypicalYear.build(main_user, 2020)

    assert actual.year.drinking_day_share[0] == round(1 / 31 * 100, 1)
    assert actual.year.intensity[0] == 10.0


@pytest.mark.parametrize("years", [1, 5])
def test_build_costs_one_query_when_nothing_is_pooled(
    main_user, years, django_assert_num_queries
):
    for year in range(2020, 2020 + years):
        DrinkFactory(date=date(year, 3, 5), stdav=5)

    with django_assert_num_queries(1):
        TypicalYear.build(main_user, 2020)


@pytest.mark.parametrize("years", [1, 5])
def test_build_costs_one_query_per_layer_however_many_years(
    main_user, years, django_assert_num_queries
):
    for year in range(2020, 2020 + years):
        DrinkFactory(date=date(year, 3, 5), stdav=5)

    with django_assert_num_queries(2):
        TypicalYear.build(main_user, 2020, PooledRange())


@pytest.mark.parametrize("drink_type", ["beer", "wine", "vodka", "stdav"])
@time_machine.travel("2026-07-15")
def test_build_is_the_same_chart_under_every_drink_type(drink_type, main_user):
    # both series are unit-free or Std Av, so the drink-type dropdown must not
    # reach this chart at all
    main_user.drink_type = drink_type
    DrinkFactory(date=date(2020, 8, 5), stdav=11.2)

    actual = TypicalYear.build(main_user, 2020)

    assert actual.year.intensity[7] == 11.2
    assert actual.year.drinking_day_share[7] == round(1 / 31 * 100, 1)


def test_build_without_records_has_no_data(main_user):
    actual = TypicalYear.build(main_user, 2020, PooledRange())

    assert not actual.has_data
    assert actual.year_from == 0


@time_machine.travel("2026-07-15")
def test_build_stops_the_running_year_at_today(main_user):
    DrinkFactory(date=date(2026, 7, 5), stdav=5)

    actual = TypicalYear.build(main_user, 2026)

    assert len(actual.year.drinking_day_share) == 7
