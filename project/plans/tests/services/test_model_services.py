import pytest
from django.urls import reverse

from ....expenses.tests.factories import ExpenseTypeFactory
from ...services.model_services import (
    ExpensePlanModelService,
    NecessaryPlanModelService,
)
from ...services.plan_rows import PlanRow
from ..factories import ExpensePlanFactory, NecessaryPlanFactory


@pytest.mark.django_db
def test_expense_row_tables_split_the_plans_by_necessity(main_user):
    necessary = ExpenseTypeFactory(title="Būstas", necessary=True)
    everyday = ExpenseTypeFactory(title="Maistas", necessary=False)
    ExpensePlanFactory(expense_type=necessary, year=1999, month=1, price=10)
    ExpensePlanFactory(expense_type=everyday, year=1999, month=2, price=20)

    tables = ExpensePlanModelService(main_user).row_tables(1999)

    assert [(row.title, row.cells[0]) for row in tables.necessary] == [
        ("Būstas", (10, "within"))
    ]
    assert [(row.title, row.cells[1]) for row in tables.everyday] == [
        ("Maistas", (20, "within"))
    ]


@pytest.mark.django_db
def test_expense_row_tables_are_empty_without_plans(main_user):
    tables = ExpensePlanModelService(main_user).row_tables(1999)

    assert tables.necessary == []
    assert tables.everyday == []


@pytest.mark.django_db
def test_necessary_plan_rows_name_the_plan_its_type_and_its_urls(main_user):
    car = ExpenseTypeFactory(title="Car")
    NecessaryPlanFactory(
        expense_type=car, title="Insurance", year=1999, month=2, price=123
    )

    rows = NecessaryPlanModelService(main_user).rows(1999)

    args = [1999, car.pk, "Insurance"]
    cells = [(0, "within")] * 12
    cells[1] = (123, "within")
    assert rows == [
        PlanRow(
            title="Insurance (Car)",
            update_url=reverse("plans:necessary_update", args=args),
            delete_url=reverse("plans:necessary_delete", args=args),
            cells=cells,
        )
    ]
