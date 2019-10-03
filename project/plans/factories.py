import factory

from ..expenses.factories import ExpenseTypeFactory
from ..incomes.factories import IncomeTypeFactory
from ..savings.factories import SavingTypeFactory
from .models import DayPlan, ExpensePlan, IncomePlan, SavingPlan


class ExpensePlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpensePlan
        django_get_or_create = ('year', 'expense_type')

    year = 1970

    expense_type = factory.SubFactory(ExpenseTypeFactory)


class IncomePlanFactory(factory.DjangoModelFactory):
    class Meta:
        model = IncomePlan
        django_get_or_create = ('year', 'income_type',)

    year = 1970
    january = 111.11
    february = 222.11

    income_type = factory.SubFactory(IncomeTypeFactory)


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
