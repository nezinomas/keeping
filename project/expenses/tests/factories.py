import factory

from ..models import Expense, ExpenseType, ExpenseName


class ExpenseTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseType
        django_get_or_create = ('title',)

    title = 'Main'
    slug = 'main'


class ExpenseNameFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseName
        django_get_or_create = ('title', 'parent',)

    parent = factory.SubFactory(ExpenseTypeFactory)
