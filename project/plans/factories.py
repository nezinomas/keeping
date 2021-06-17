import factory

from ..expenses.factories import ExpenseTypeFactory
from ..incomes.factories import IncomeTypeFactory
from ..journals.factories import JournalFactory
from ..savings.factories import SavingTypeFactory
from .models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan


class ExpensePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpensePlan
        django_get_or_create = ('year', 'expense_type', 'journal', )

    year = 1999

    expense_type = factory.SubFactory(ExpenseTypeFactory)
    journal = factory.SubFactory(JournalFactory)


class IncomePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IncomePlan
        django_get_or_create = ('year', 'income_type', 'journal', )

    year = 1999
    january = 111.11
    february = 222.11

    income_type = factory.SubFactory(IncomeTypeFactory)
    journal = factory.SubFactory(JournalFactory)


class SavingPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingPlan
        django_get_or_create = ('year', 'saving_type', 'journal', )

    year = 1999
    january = 32.33
    february = 32.33

    saving_type = factory.SubFactory(SavingTypeFactory)
    journal = factory.SubFactory(JournalFactory)


class DayPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DayPlan

    year = 1999
    january = 32.33
    february = 32.33
    journal = factory.SubFactory(JournalFactory)


class NecessaryPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NecessaryPlan

    year = 1999
    title = 'other'
    january = 15.0
    february = 15.0
    journal = factory.SubFactory(JournalFactory)
