import json
from datetime import date

import pytest

from ...services.year_comparison import YearComparison, YearComparisonChartViewModel
from ..factories import DrinkFactory

pytestmark = pytest.mark.django_db


def test_build_returns_a_chart_view_model(main_user):
    actual = YearComparison.build(main_user, [1999])

    assert isinstance(actual, YearComparisonChartViewModel)
    assert actual.title
    assert len(actual.categories) == 12


def test_series_per_year_with_records(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)
    DrinkFactory(date=date(2000, 1, 1), stdav=25)

    actual = YearComparison.build(main_user, [1999, 2000])

    assert [s["name"] for s in actual.serries] == [1999, 2000]
    assert round(actual.serries[0]["data"][0], 2) == 16.13
    assert round(actual.serries[1]["data"][0], 2) == 161.29


def test_years_without_records_drop_out(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, [1998, 1999, 2000])

    assert [s["name"] for s in actual.serries] == [1999]


def test_no_records_at_all(main_user):
    actual = YearComparison.build(main_user, [1999, 2000])

    assert actual.serries == []
    assert actual.has_data is False


def test_has_data(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    assert YearComparison.build(main_user, [1999]).has_data is True


def test_accepts_a_range(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, range(1998, 2001))

    assert [s["name"] for s in actual.serries] == [1999]


def test_accepts_year_strings(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, ["1999"])

    assert len(actual.serries) == 1


def test_only_the_users_own_records(main_user, second_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5, user=second_user)

    actual = YearComparison.build(main_user, [1999])

    assert actual.has_data is False


def test_as_dict_is_json_serializable(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, [1999]).as_dict

    assert set(actual) == {"title", "categories", "serries", "unit", "decimals"}
    assert json.dumps(actual)


def test_series_data_covers_twelve_months(main_user):
    DrinkFactory(date=date(1999, 1, 1), stdav=2.5)

    actual = YearComparison.build(main_user, [1999])

    assert len(actual.serries[0]["data"]) == 12
