from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser

from ...services.model_services import IncomeModelService, IncomeTypeModelService
from ..factories import IncomeFactory, IncomeTypeFactory


def test_income_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        IncomeModelService(user=None)


def test_income_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        IncomeModelService(user=anon)


@pytest.mark.django_db
def test_income_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    IncomeModelService(user=main_user)


def test_income_type_init_raises_if_no_user():
    with pytest.raises(ValueError, match="User required"):
        IncomeTypeModelService(user=None)


def test_income_type_init_raises_if_anonymous_user():
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        IncomeTypeModelService(user=anon)


@pytest.mark.django_db
def test_income_type_init_succeeds_with_real_user(main_user):
    # No need to save — just check __init__
    IncomeTypeModelService(user=main_user)


@pytest.mark.django_db
def test_sum_by_type_between_sums_each_type_largest_first(main_user):
    alga = IncomeTypeFactory(title="Alga")
    kita = IncomeTypeFactory(title="Kita")
    IncomeFactory(date=date(1999, 1, 5), price=100, income_type=kita)
    IncomeFactory(date=date(1999, 2, 5), price=300, income_type=alga)
    IncomeFactory(date=date(1999, 3, 5), price=200, income_type=alga)
    IncomeFactory(date=date(1999, 3, 6), price=999, income_type=alga)
    IncomeFactory(date=date(1998, 12, 31), price=999, income_type=alga)

    actual = IncomeModelService(main_user).sum_by_type_between(
        date(1999, 1, 1), date(1999, 3, 5)
    )

    assert list(actual) == [
        {"title": "Alga", "sum": 500},
        {"title": "Kita", "sum": 100},
    ]


@pytest.mark.django_db
def test_sum_by_month_between_sums_each_month_in_order(main_user):
    IncomeFactory(date=date(1999, 3, 5), price=200)
    IncomeFactory(date=date(1999, 1, 5), price=100)
    IncomeFactory(date=date(1999, 1, 20), price=50)
    IncomeFactory(date=date(1999, 3, 6), price=999)

    actual = IncomeModelService(main_user).sum_by_month_between(
        date(1999, 1, 1), date(1999, 3, 5)
    )

    assert list(actual) == [
        {"date": date(1999, 1, 1), "sum": 150},
        {"date": date(1999, 3, 1), "sum": 200},
    ]


@pytest.mark.django_db
def test_last_date_by_type_gives_each_type_its_latest_income(main_user):
    alga = IncomeTypeFactory(title="Alga")
    kita = IncomeTypeFactory(title="Kita")
    IncomeFactory(date=date(1999, 3, 5), income_type=alga)
    IncomeFactory(date=date(1999, 1, 5), income_type=alga)
    IncomeFactory(date=date(1998, 6, 1), income_type=kita)

    actual = IncomeModelService(main_user).last_date_by_type(date(1999, 12, 31))

    assert sorted(actual, key=lambda row: row["title"]) == [
        {"title": "Alga", "date": date(1999, 3, 5)},
        {"title": "Kita", "date": date(1998, 6, 1)},
    ]


@pytest.mark.django_db
def test_last_date_by_type_stops_at_the_given_day(main_user):
    alga = IncomeTypeFactory(title="Alga")
    IncomeFactory(date=date(1999, 3, 5), income_type=alga)
    IncomeFactory(date=date(2000, 1, 5), income_type=alga)

    actual = IncomeModelService(main_user).last_date_by_type(date(1999, 12, 31))

    assert list(actual) == [{"title": "Alga", "date": date(1999, 3, 5)}]


def test_income_type_model_service_promises_no_year():
    assert not hasattr(IncomeTypeModelService, "year")
