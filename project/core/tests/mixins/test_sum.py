from datetime import date

import pytest
from django.core.exceptions import FieldError

from ....incomes.models import Income
from ....incomes.tests.factories import IncomeFactory
from ...mixins.sum import SumMixin


class DummySumService(SumMixin):
    pass


@pytest.fixture
def service():
    return DummySumService()


@pytest.fixture
def base_qs():
    return Income.objects.all()


@pytest.fixture
def populate_data():
    """
    Creates a specific dataset using factories to test groupings and sums.
    1999: Total 55 (across 2 rows)
    2000: Total 150 (across 2 rows)
    """
    IncomeFactory(date=date(1999, 1, 15), price=25)
    IncomeFactory(date=date(1999, 1, 20), price=30)

    IncomeFactory(date=date(2000, 5, 10), price=100)
    IncomeFactory(date=date(2000, 6, 15), price=50)


@pytest.mark.django_db
def test_year_sum_groups_and_sums_all_years(service, base_qs, populate_data):
    actual = list(service.year_sum(qs=base_qs))

    assert len(actual) == 2
    assert actual[0] == {"year": 1999, "sum": 55}
    assert actual[1] == {"year": 2000, "sum": 150}


@pytest.mark.django_db
def test_year_sum_filters_by_specific_year(service, base_qs, populate_data):
    actual = list(service.year_sum(qs=base_qs, year=1999))

    assert len(actual) == 1
    assert actual[0] == {"year": 1999, "sum": 55}


@pytest.mark.django_db
def test_month_sum_groups_by_month_for_given_year(service, base_qs, populate_data):
    actual = list(service.month_sum(qs=base_qs, year=2000))

    assert len(actual) == 2
    assert actual[0] == {"date": date(2000, 5, 1), "sum": 100}
    assert actual[1] == {"date": date(2000, 6, 1), "sum": 50}


@pytest.mark.django_db
def test_month_sum_filters_by_specific_month(service, base_qs, populate_data):
    actual = list(service.month_sum(qs=base_qs, year=2000, month=5))

    assert len(actual) == 1
    assert actual[0] == {"date": date(2000, 5, 1), "sum": 100}


@pytest.mark.django_db
def test_day_sum_groups_by_specific_day(service, base_qs, populate_data):
    actual = list(service.day_sum(qs=base_qs, year=1999, month=1))

    assert len(actual) == 2
    assert actual[0] == {"date": date(1999, 1, 15), "sum": 25}
    assert actual[1] == {"date": date(1999, 1, 20), "sum": 30}


@pytest.mark.django_db
def test_empty_queryset_returns_empty_list(service, base_qs):
    actual = list(service.year_sum(qs=base_qs))

    assert len(actual) == 0
    assert actual == []


@pytest.mark.django_db
def test_summing_zero_values(service, base_qs):
    IncomeFactory(date=date(2026, 1, 1), price=0.0)
    IncomeFactory(date=date(2026, 1, 2), price=0.0)

    actual = list(service.year_sum(qs=base_qs))

    assert len(actual) == 1
    assert actual[0] == {"year": 2026, "sum": 0.0}


@pytest.mark.django_db
def test_invalid_sum_column_raises_field_error(service, base_qs, populate_data):
    with pytest.raises(FieldError):
        list(service.year_sum(qs=base_qs, sum_column="column_that_does_not_exist"))


@pytest.mark.django_db
def test_invalid_filter_kwarg_raises_field_error(service, base_qs):
    with pytest.raises(FieldError):
        list(service.year_filter(qs=base_qs, year=1999, field="fake_date_field"))
