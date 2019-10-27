from datetime import date as dt
from decimal import Decimal

import factory
from django.db.models.signals import post_save

from ..accounts.factories import AccountFactory
from .models import Expense, ExpenseName, ExpenseType


@factory.django.mute_signals(post_save)
class ExpenseTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseType
        django_get_or_create = ('title',)

    title = 'Expense Type'


@factory.django.mute_signals(post_save)
class ExpenseNameFactory(factory.DjangoModelFactory):
    class Meta:
        model = ExpenseName
        django_get_or_create = ('title', 'parent',)

    title = 'Expense Name'
    parent = factory.SubFactory(ExpenseTypeFactory)


@factory.django.mute_signals(post_save)
class ExpenseFactory(factory.DjangoModelFactory):
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
