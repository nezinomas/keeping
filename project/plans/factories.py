import factory
from django.db.models.signals import post_save

from ..expenses.factories import ExpenseTypeFactory
from ..incomes.factories import IncomeTypeFactory
from ..savings.factories import SavingTypeFactory
from .models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan


@factory.django.mute_signals(post_save)
class ExpensePlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpensePlan
        django_get_or_create = ('year', 'expense_type')

    year = 1970

    expense_type = factory.SubFactory(ExpenseTypeFactory)


@factory.django.mute_signals(post_save)
class IncomePlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = IncomePlan
        django_get_or_create = ('year', 'income_type',)

    year = 1970
    january = 111.11
    february = 222.11

    income_type = factory.SubFactory(IncomeTypeFactory)


@factory.django.mute_signals(post_save)
class SavingPlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavingPlan
        django_get_or_create = ('year', 'saving_type',)

    year = 1970
    january = 32.33
    february = 32.33

    saving_type = factory.SubFactory(SavingTypeFactory)


class DayPlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = DayPlan

    year = 1970
    january = 32.33
    february = 32.33


class NecessaryPlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = NecessaryPlan

    year = 1970
    title = 'other'
    january = 15.0
    february = 15.0
