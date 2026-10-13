import json
from datetime import date

import pytest

from ...services.year_comparison import YearComparison, YearComparisonChartViewModel
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db

TODAY = date(2001, 1, 1)


def test_series_per_year_with_records(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)
    DrinkFactory(date=date(2000, 1, 1), stdav=25)

    actual = YearComparison.build(main_user, [1999, 2000], TODAY)

    assert [s["name"] for s in actual.serries] == [1999, 2000]
    assert round(actual.serries[0]["data"][0], 2) == 16.13
    assert round(actual.serries[1]["data"][0], 2) == 161.29


def test_years_without_records_drop_out(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, [1998, 1999, 2000], TODAY)

    assert [s["name"] for s in actual.serries] == [1999]


@pytest.mark.parametrize(
    "drinks, has_data",
    [
        pytest.param([], False, id="no_records_at_all"),
        pytest.param([("main", date(1999, 1, 1))], True, id="a_record"),
        pytest.param([("second", date(1999, 1, 1))], False, id="only_the_users_own"),
    ],
)
def test_has_data(main_user, second_user, drinks, has_data):
    owners = {"main": main_user, "second": second_user}
    for owner, day in drinks:
        DrinkFactory(date=day, stdav=2.5, user=owners[owner])

    actual = YearComparison.build(main_user, [1999, 2000], TODAY)

    assert actual.has_data is has_data
    assert (actual.serries == []) is (not has_data)


@pytest.mark.parametrize(
    "years, names",
    [
        pytest.param(range(1998, 2001), [1999], id="a_range"),
        pytest.param(["1999"], ["1999"], id="year_strings"),
    ],
)
def test_accepts(main_user, years, names):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, years, TODAY)

    assert [s["name"] for s in actual.serries] == names


def test_as_dict_is_json_serializable(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, [1999], TODAY).as_dict

    assert json.dumps(actual)


@pytest.mark.parametrize(
    "today, months",
    [
        pytest.param("1999-06-15", 6, id="running_year_ends_in_june"),
        pytest.param("2000-03-01", 12, id="finished_year_runs_to_december"),
    ],
)
def test_series_data_ends_at_the_month_reached(main_user, today, months):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)
    actual = YearComparison.build(main_user, [1999], date.fromisoformat(today))

    assert len(actual.serries[0]["data"]) == months


# YearComparison.for_pair
def test_a_pair_both_years_on_record(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)
    DrinkFactory(date=date(2000, 1, 1), stdav=25)

    actual = YearComparison.for_pair(main_user, 1999, 2000, TODAY)

    assert [s["name"] for s in actual.serries] == [1999, 2000]
    assert actual.has_data is True


@pytest.mark.parametrize(
    "drink_years",
    [pytest.param([1999], id="missing_one_year"), pytest.param([], id="missing_both")],
)
def test_a_pair_missing_a_year_draws_nothing(main_user, drink_years):
    for year in drink_years:
        DrinkFactory(date=date(year, 1, 1), stdav=2.5)

    actual = YearComparison.for_pair(main_user, 1999, 2000, TODAY)

    assert actual.has_data is False


def test_a_pair_that_draws_nothing_is_still_a_chart_view_model(main_user):
    actual = YearComparison.for_pair(main_user, 1999, 2000, TODAY)

    assert isinstance(actual, YearComparisonChartViewModel)
    assert len(actual.categories) == 12


# YearComparison.for_recent
def test_recent_years_end_with_the_header_year(main_user):
    DrinkFactory(date=date(1998, 1, 1), stdav=2.5)
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)
    DrinkFactory(date=date(2000, 1, 1), stdav=2.5)

    actual = YearComparison.for_recent(main_user, 1999, 2, TODAY)

    assert [s["name"] for s in actual.serries] == [1998, 1999]


@pytest.mark.parametrize(
    "qty",
    [
        pytest.param(1, id="recent_years_of_one_is_the_header_year_alone"),
        pytest.param(5, id="recent_years_are_best_effort"),
    ],
)
def test_recent_years_reach_back_only_as_far_as_the_records(main_user, qty):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.for_recent(main_user, 1999, qty, TODAY)

    assert [s["name"] for s in actual.serries] == [1999]


def test_recent_years_of_none_draws_nothing(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.for_recent(main_user, 1999, 0, TODAY)

    assert actual.has_data is False
