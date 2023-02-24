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

    journal = factory.SubFactory(JournalFactory)
    expense_type = factory.SubFactory(ExpenseTypeFactory)
    year = 1999
    january = 1
    february = 1
    march = 1
    april = 1
    may = 1
    june = 1
    july = 1
    august = 1
    september = 1
    october = 1
    november = 1
    december = 1


class IncomePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IncomePlan
        django_get_or_create = ('year', 'income_type', 'journal', )

    journal = factory.SubFactory(JournalFactory)
    income_type = factory.SubFactory(IncomeTypeFactory)
    year = 1999
    january = 1
    february = 1
    march = 1
    april = 1
    may = 1
    june = 1
    july = 1
    august = 1
    september = 1
    october = 1
    november = 1
    december = 1


class SavingPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingPlan
        django_get_or_create = ('year', 'saving_type', 'journal', )

    journal = factory.SubFactory(JournalFactory)
    saving_type = factory.SubFactory(SavingTypeFactory)
    year = 1999
    january = 1
    february = 1
    march = 1
    april = 1
    may = 1
    june = 1
    july = 1
    august = 1
    september = 1
    october = 1
    november = 1
    december = 1


class DayPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DayPlan

    journal = factory.SubFactory(JournalFactory)
    year = 1999
    january = 1
    february = 1
    march = 1
    april = 1
    may = 1
    june = 1
    july = 1
    august = 1
    september = 1
    october = 1
    november = 1
    december = 1


class NecessaryPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NecessaryPlan

    journal = factory.SubFactory(JournalFactory)
    year = 1999
    title = 'other'
    january = 1
    february = 1
    march = 1
    april = 1
    may = 1
    june = 1
    july = 1
    august = 1
    september = 1
    october = 1
    november = 1
    december = 1
