from typing import NamedTuple

import factory

from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...journals.tests.factories import JournalFactory
from ...savings.tests.factories import SavingTypeFactory
from ..forms import (
    DayPlanForm,
    ExpensePlanForm,
    IncomePlanForm,
    NecessaryPlanForm,
    SavingPlanForm,
)
from ..models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan


class ExpensePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpensePlan

    journal = factory.SubFactory(JournalFactory)
    expense_type = factory.SubFactory(ExpenseTypeFactory)
    year = 1999
    month = 1
    price = 1


class IncomePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IncomePlan

    journal = factory.SubFactory(JournalFactory)
    income_type = factory.SubFactory(IncomeTypeFactory)
    year = 1999
    month = 1
    price = 1


class SavingPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingPlan

    journal = factory.SubFactory(JournalFactory)
    saving_type = factory.SubFactory(SavingTypeFactory)
    year = 1999
    month = 1
    price = 1


class DayPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DayPlan

    journal = factory.SubFactory(JournalFactory)
    year = 1999
    month = 1
    price = 1


class NecessaryPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NecessaryPlan

    journal = factory.SubFactory(JournalFactory)
    expense_type = factory.SubFactory(ExpenseTypeFactory)
    year = 1999
    title = "other"
    month = 1
    price = 1


class PlanKind(NamedTuple):
    factory: type
    form: type
    grouping: tuple[str, ...]
    type_factories: dict  # grouping field -> factory of the row it points to
    extra: dict  # plain grouping values, such as a title

    @property
    def model(self):
        return self.factory._meta.model


PLAN_KINDS = [
    PlanKind(
        IncomePlanFactory,
        IncomePlanForm,
        ("income_type",),
        {"income_type": IncomeTypeFactory},
        {},
    ),
    PlanKind(
        ExpensePlanFactory,
        ExpensePlanForm,
        ("expense_type",),
        {"expense_type": ExpenseTypeFactory},
        {},
    ),
    PlanKind(
        SavingPlanFactory,
        SavingPlanForm,
        ("saving_type",),
        {"saving_type": SavingTypeFactory},
        {},
    ),
    PlanKind(DayPlanFactory, DayPlanForm, (), {}, {}),
    PlanKind(
        NecessaryPlanFactory,
        NecessaryPlanForm,
        ("expense_type", "title"),
        {"expense_type": ExpenseTypeFactory},
        {"title": "Rent"},
    ),
]
