from datetime import date as dt
from decimal import Decimal

import factory

from ..journals.factories import JournalFactory
from .models import Pension, PensionBalance, PensionType


class PensionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PensionType
        django_get_or_create = ('title',)

    title = 'PensionType'
    journal = factory.SubFactory(JournalFactory)


class PensionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pension

    date = dt(1999, 1, 1)
    price = Decimal(100)
    fee = Decimal(1.01)
    remark = 'remark'
    pension_type = factory.SubFactory(PensionTypeFactory)


class PensionBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PensionBalance

    year = 1999
    pension_type = factory.SubFactory(PensionTypeFactory)

    past_amount = 2.0
    past_fee = 2.1
    fees = 2.2
    invested = 2.3
    incomes = 2.4
    market_value = 2.5
    profit_incomes_proc = 2.6
    profit_incomes_sum = 2.7
    profit_invested_proc = 2.8
    profit_invested_sum = 2.9
