from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.tests.factories import AccountFactory
from .models import Expense, ExpenseName, ExpenseType


class ExpenseTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseType
        django_get_or_create = ('title',)

    title = 'Expense Type'


class ExpenseNameFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseName
        django_get_or_create = ('title', 'parent',)

    title = 'Expense Name'
    parent = factory.SubFactory(ExpenseTypeFactory)


class ExpenseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Expense

    date = dt(1999, 1, 1)
    price = Decimal(1.12)
    quantity = 13
    expense_type = factory.SubFactory(ExpenseTypeFactory)
    expense_name = factory.SubFactory(ExpenseNameFactory)
    remark = 'Remark'
    exception = True
    account = factory.SubFactory(AccountFactory)
