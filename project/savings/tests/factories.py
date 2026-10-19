from datetime import date as dt

import factory
from django.db.models import signals

from ...accounts.tests.factories import AccountFactory
from ...journals.tests.factories import JournalFactory
from ..models import Saving, SavingBalance, SavingType


class SavingTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingType
        django_get_or_create = ("title",)

    title = "Savings"
    journal = factory.SubFactory(JournalFactory)


class SavingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Saving

    date = dt(1999, 1, 1)
    price = 150
    fee = 5
    remark = "remark"
    saving_type = factory.SubFactory(SavingTypeFactory)
    account = factory.SubFactory(AccountFactory)


@factory.django.mute_signals(signals.post_save)
class SavingBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingBalance

    year = 1999
    saving_type = factory.SubFactory(SavingTypeFactory)

    past_amount = 20
    past_fee = 21
    fee = 22
    incomes = 24
    market_value = 25
    profit_sum = 29
    profit_proc = 30.3
