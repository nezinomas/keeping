import factory

from ...expenses.tests.factories import ExpenseTypeFactory
from ...incomes.tests.factories import IncomeTypeFactory
from ...journals.tests.factories import JournalFactory
from ...savings.tests.factories import SavingTypeFactory
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
