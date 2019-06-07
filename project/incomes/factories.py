from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from .models import Income, IncomeType


class IncomeTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = IncomeType
        django_get_or_create = ('title',)

    title = 'Income Type'


class IncomeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Income

    date = dt(1999, 1, 1)
    amount = Decimal(1000.62)
    remark = 'remark'
    account = factory.SubFactory(AccountFactory)
    income_type = factory.SubFactory(IncomeTypeFactory)
