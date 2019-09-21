import factory

from .models import (
    DayPlan, ExpensePlan, ExpenseType, IncomePlan, IncomeType, SavingPlan,
    SavingType)


class ExpenseTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseType
        django_get_or_create = ('title',)

    necessary = False

    @factory.sequence
    def title(n):
        return 'expense-type-{n}'.format(n=n)


class IncomeTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = IncomeType
        django_get_or_create = ('title',)

    @factory.sequence
    def title(n):
        return 'income-type-{n}'.format(n=n)


class SavingTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavingType
        django_get_or_create = ('title',)

    @factory.sequence
    def title(n):
        return 'saving-type-{n}'.format(n=n)


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
