from datetime import date as dt

import factory

from ..accounts.factories import AccountFactory
from ..journals.factories import JournalFactory
from .models import Expense, ExpenseName, ExpenseType


class ExpenseTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpenseType
        django_get_or_create = ('title',)

    journal = factory.SubFactory(JournalFactory)
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
    account = factory.SubFactory(AccountFactory)
    expense_type = factory.SubFactory(ExpenseTypeFactory)
    expense_name = factory.SubFactory(ExpenseNameFactory)
    price = 112
    quantity = 13
    remark = 'Remark'
    exception = False
