from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from ..users.factories import UserFactory
from .models import Expense, ExpenseName, ExpenseType


class ExpenseTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseType
        django_get_or_create = ('title',)

    user = factory.SubFactory(UserFactory)
    title = 'Expense Type'


class ExpenseNameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseName
        django_get_or_create = ('title', 'parent',)

    title = 'Expense Name'
    parent = factory.SubFactory(ExpenseTypeFactory)


class ExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Expense

    date = dt(1999, 1, 1)
    price = Decimal(1.12)
    quantity = 13
    expense_type = factory.SubFactory(ExpenseTypeFactory)
    expense_name = factory.SubFactory(ExpenseNameFactory)
    remark = 'Remark'
    exception = False
    account = factory.SubFactory(AccountFactory)
