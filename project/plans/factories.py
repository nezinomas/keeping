import factory
from django.db.models.signals import post_save

from ..expenses.factories import ExpenseTypeFactory
from ..incomes.factories import IncomeTypeFactory
from ..savings.factories import SavingTypeFactory
from .models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan
from ..users.factories import UserFactory


@factory.django.mute_signals(post_save)
class ExpensePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpensePlan
        django_get_or_create = ('year', 'expense_type', 'user', )

    year = 1999

    expense_type = factory.SubFactory(ExpenseTypeFactory)
    user = factory.SubFactory(UserFactory)


@factory.django.mute_signals(post_save)
class IncomePlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IncomePlan
        django_get_or_create = ('year', 'income_type', 'user', )

    year = 1999
    january = 111.11
    february = 222.11

    income_type = factory.SubFactory(IncomeTypeFactory)
    user = factory.SubFactory(UserFactory)


@factory.django.mute_signals(post_save)
class SavingPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingPlan
        django_get_or_create = ('year', 'saving_type', 'user', )

    year = 1999
    january = 32.33
    february = 32.33

    saving_type = factory.SubFactory(SavingTypeFactory)
    user = factory.SubFactory(UserFactory)


class DayPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DayPlan

    year = 1999
    january = 32.33
    february = 32.33
    user = factory.SubFactory(UserFactory)


class NecessaryPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NecessaryPlan

    year = 1999
    title = 'other'
    january = 15.0
    february = 15.0
    user = factory.SubFactory(UserFactory)
