from datetime import date

import pytest

from ....expenses.services.model_services import ExpenseModelService
from ....expenses.tests.factories import (
    ExpenseFactory,
    ExpenseNameFactory,
    ExpenseTypeFactory,
)
from ....incomes.services.model_services import IncomeModelService
from ....incomes.tests.factories import IncomeFactory, IncomeTypeFactory


def _income_group(title):
    return IncomeTypeFactory(title=title)


def _income_row(group, **kwargs):
    return IncomeFactory(income_type=group, **kwargs)


def _expense_group(title):
    return ExpenseNameFactory(title=title, parent=ExpenseTypeFactory(title="Maistas"))


def _expense_row(group, **kwargs):
    return ExpenseFactory(expense_name=group, expense_type=group.parent, **kwargs)


# one case per model: its service, the grouping field, and how to make a group and a row
models = pytest.mark.parametrize(
    "service, field, make_group, make_row",
    [
        (IncomeModelService, "income_type", _income_group, _income_row),
        (ExpenseModelService, "expense_name", _expense_group, _expense_row),
    ],
    ids=["income_type", "expense_name"],
)


@pytest.mark.django_db
@models
def test_sum_by_between_sums_each_group_largest_first(
    main_user, service, field, make_group, make_row
):
    alga = make_group("Alga")
    kita = make_group("Kita")
    make_row(kita, date=date(1999, 1, 5), price=100)
    make_row(kita, date=date(1999, 1, 1), price=7)
    make_row(alga, date=date(1999, 2, 5), price=300)
    make_row(alga, date=date(1999, 3, 5), price=200)
    make_row(alga, date=date(1999, 3, 6), price=999)
    make_row(alga, date=date(1998, 12, 31), price=999)

    actual = service(main_user).sum_by_between(
        field, date(1999, 1, 1), date(1999, 3, 5)
    )

    assert list(actual) == [
        {"pk": alga.pk, "title": "Alga", "sum": 500},
        {"pk": kita.pk, "title": "Kita", "sum": 107},
    ]


@pytest.mark.django_db
def test_sum_by_month_between_sums_each_month_in_order(main_user):
    IncomeFactory(date=date(1999, 3, 5), price=200)
    IncomeFactory(date=date(1999, 1, 5), price=100)
    IncomeFactory(date=date(1999, 1, 20), price=50)
    IncomeFactory(date=date(1999, 3, 6), price=999)
    IncomeFactory(date=date(1998, 12, 31), price=999)

    actual = IncomeModelService(main_user).sum_by_month_between(
        date(1999, 1, 1), date(1999, 3, 5)
    )

    assert list(actual) == [
        {"date": date(1999, 1, 1), "sum": 150},
        {"date": date(1999, 3, 1), "sum": 200},
    ]


@pytest.mark.django_db
@models
def test_last_date_by_gives_each_group_its_latest_row(
    main_user, service, field, make_group, make_row
):
    alga = make_group("Alga")
    kita = make_group("Kita")
    make_row(alga, date=date(1999, 3, 5))
    make_row(alga, date=date(1999, 1, 5))
    make_row(kita, date=date(1998, 6, 1))

    actual = service(main_user).last_date_by(field, date(1999, 12, 31))

    assert sorted(actual, key=lambda row: row["title"]) == [
        {"pk": alga.pk, "title": "Alga", "date": date(1999, 3, 5)},
        {"pk": kita.pk, "title": "Kita", "date": date(1998, 6, 1)},
    ]


@pytest.mark.django_db
@models
def test_last_date_by_stops_at_the_given_day(
    main_user, service, field, make_group, make_row
):
    alga = make_group("Alga")
    make_row(alga, date=date(1999, 12, 31))
    make_row(alga, date=date(2000, 1, 5))

    actual = service(main_user).last_date_by(field, date(1999, 12, 31))

    assert list(actual) == [
        {"pk": alga.pk, "title": "Alga", "date": date(1999, 12, 31)}
    ]
