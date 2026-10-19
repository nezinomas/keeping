from datetime import date as dt

import factory
from django.db.models import signals

from ...journals.tests.factories import JournalFactory
from ..models import Pension, PensionBalance, PensionType


class PensionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PensionType
        django_get_or_create = ("title",)

    title = "PensionType"
    journal = factory.SubFactory(JournalFactory)


class PensionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pension

    date = dt(1999, 1, 1)
    price = 100
    fee = 1
    remark = "remark"
    pension_type = factory.SubFactory(PensionTypeFactory)


@factory.django.mute_signals(signals.post_save)
class PensionBalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PensionBalance

    year = 1999
    pension_type = factory.SubFactory(PensionTypeFactory)

    past_amount = 20
    past_fee = 21
    fee = 22
    incomes = 24
    market_value = 25
    profit_sum = 29
    profit_proc = 30.3
