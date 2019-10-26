from datetime import date as dt
from decimal import Decimal

import factory
from django.db.models.signals import post_save

from ..accounts.factories import AccountFactory
from .models import Saving, SavingType, SavingBalance


class SavingTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavingType
        django_get_or_create = ('title',)

    title = 'Savings'


@factory.django.mute_signals(post_save)
class SavingFactory(factory.DjangoModelFactory):
    class Meta:
        model = Saving

    date = dt(1999, 1, 1)
    price = Decimal(150)
    fee = Decimal(5.55)
    remark = 'remark'
    saving_type = factory.SubFactory(SavingTypeFactory)
    account = factory.SubFactory(AccountFactory)


class SavingBalanceFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavingBalance

    year = 1999
    saving_type = factory.SubFactory(SavingTypeFactory)

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
