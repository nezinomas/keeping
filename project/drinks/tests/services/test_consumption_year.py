from datetime import date

import pytest

from ...lib.drinks_stats import DataRow
from ...services.consumption_year import ConsumptionYear
from ..factories import DrinkFactory, DrinkTargetFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name="_records")
def fixture_records(second_user):
    DrinkFactory(date=date(1998, 12, 20), stdav=1.0)
    DrinkFactory(date=date(1999, 1, 1), stdav=1.0)
    DrinkFactory(date=date(1999, 1, 1), stdav=1.5)
    DrinkFactory(date=date(1999, 2, 10), stdav=2.0)
    DrinkFactory(date=date(1999, 3, 5), stdav=3.0, user=second_user)


def test_daily_returns_data_rows(main_user, _records):
    actual = ConsumptionYear(main_user, 1999).daily

    assert all(isinstance(row, DataRow) for row in actual)
    assert [row.date for row in actual] == [date(1999, 1, 1), date(1999, 2, 10)]
    assert [row.stdav for row in actual] == [2.5, 2.0]


def test_daily_rows_stay_dicts_for_core_modules(main_user, _records):
    actual = ConsumptionYear(main_user, 1999).daily_rows

    assert all(isinstance(row, dict) for row in actual)
    assert set(actual[0]) == {"date", "stdav", "qty"}


def test_monthly_returns_data_rows(main_user, _records):
    actual = ConsumptionYear(main_user, 1999).monthly

    assert all(isinstance(row, DataRow) for row in actual)
    assert [row.stdav for row in actual] == [2.5, 2.0]


def test_only_the_users_own_records(main_user, _records):
    actual = ConsumptionYear(main_user, 1999).daily

    assert len(actual) == 2


def test_empty_year(main_user, _records):
    records = ConsumptionYear(main_user, 2000)

    assert records.daily == []
    assert records.monthly == []
    assert records.has_data is False


def test_has_data(main_user, _records):
    assert ConsumptionYear(main_user, 1999).has_data is True


def test_converter_follows_the_users_drink_type(main_user):
    main_user.drink_type = "wine"
    main_user.save()

    actual = ConsumptionYear(main_user, 1999).converter

    assert actual.drink_type == "wine"
    assert actual.servings_to_stdav(1) == 8


def test_last_recorded_date(main_user, _records):
    actual = ConsumptionYear(main_user, 1999).last_recorded_date

    assert actual == date(1999, 2, 10)


def test_last_recorded_date_when_year_is_empty(main_user, _records):
    assert ConsumptionYear(main_user, 2000).last_recorded_date is None


def test_last_recorded_date_before(main_user, _records):
    actual = ConsumptionYear(main_user, 1999).last_recorded_date_before

    assert actual == date(1998, 12, 20)


def test_last_recorded_date_before_when_nothing_earlier(main_user, _records):
    assert ConsumptionYear(main_user, 1998).last_recorded_date_before is None


def test_previous_is_the_year_before(main_user, _records):
    records = ConsumptionYear(main_user, 1999)

    assert records.previous.year == 1998
    assert [row.date for row in records.previous.daily] == [date(1998, 12, 20)]


def test_previous_carries_the_same_user(main_user, _records):
    records = ConsumptionYear(main_user, 1999)

    assert records.previous.user == main_user


def test_target(main_user):
    DrinkTargetFactory(year=1999, quantity=500, drink_type="beer")

    actual = ConsumptionYear(main_user, 1999).target

    assert actual.has_data is True
    assert actual.qty == 500.0


def test_target_when_none_set(main_user):
    actual = ConsumptionYear(main_user, 1999).target

    assert actual.has_data is False
    assert actual.qty == 0.0
    assert actual.target_id == 0


def test_readers_are_cached(main_user, _records, django_assert_num_queries):
    records = ConsumptionYear(main_user, 1999)

    with django_assert_num_queries(1):
        records.daily
        records.daily
        records.daily_rows
