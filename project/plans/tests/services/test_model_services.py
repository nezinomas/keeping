import pytest
from django.contrib.auth.models import AnonymousUser

from ....expenses.tests.factories import ExpenseTypeFactory
from ...services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)
from ..factories import ExpensePlanFactory


@pytest.mark.parametrize(
    "model",
    [
        (DayPlanModelService),
        (IncomePlanModelService),
        (SavingPlanModelService),
        (ExpensePlanModelService),
        (NecessaryPlanModelService),
    ],
)
def test_init_raises_if_no_user(model):
    with pytest.raises(ValueError, match="User required"):
        model(user=None)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlanModelService),
        (IncomePlanModelService),
        (SavingPlanModelService),
        (ExpensePlanModelService),
        (NecessaryPlanModelService),
    ],
)
def test_init_raises_if_anonymous_user(model):
    anon = AnonymousUser()
    with pytest.raises(ValueError, match="Authenticated user required"):
        model(user=anon)


@pytest.mark.parametrize(
    "model",
    [
        (DayPlanModelService),
        (IncomePlanModelService),
        (SavingPlanModelService),
        (ExpensePlanModelService),
        (NecessaryPlanModelService),
    ],
)
@pytest.mark.django_db
def test_init_succeeds_with_real_user(model, main_user):
    # No need to save — just check __init__
    model(user=main_user)


@pytest.mark.django_db
def test_expense_pivot_tables_split_the_plans_by_necessity(main_user):
    necessary = ExpenseTypeFactory(title="Būstas", necessary=True)
    everyday = ExpenseTypeFactory(title="Maistas", necessary=False)
    ExpensePlanFactory(expense_type=necessary, year=1999, month=1, price=10)
    ExpensePlanFactory(expense_type=everyday, year=1999, month=2, price=20)

    tables = ExpensePlanModelService(main_user).pivot_tables(1999)

    assert tables.necessary == {necessary: {1: 10}}
    assert tables.everyday == {everyday: {2: 20}}


@pytest.mark.django_db
def test_expense_pivot_tables_are_empty_without_plans(main_user):
    tables = ExpensePlanModelService(main_user).pivot_tables(1999)

    assert tables.necessary == {}
    assert tables.everyday == {}
