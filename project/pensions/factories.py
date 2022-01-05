from datetime import date as dt
from datetime import datetime
from decimal import Decimal

import factory
import pytz
from django.db import models
from django.db.models import signals

from ..journals.factories import JournalFactory
from .models import Pension, PensionBalance, PensionType


class PensionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PensionType
        django_get_or_create = ('title',)

    title = 'PensionType'
    journal = factory.SubFactory(JournalFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        created = kwargs.pop('created', None)

        obj = super()._create(target_class, *args, **kwargs)

        if created is not None:
            obj.created = created
        else:
            obj.created = datetime(1, 1, 1, tzinfo=pytz.utc)

        models.Model.save(obj)

        return obj

class PensionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pension

    date = dt(1999, 1, 1)
    price = Decimal(100)
    fee = Decimal(1.01)
    remark = 'remark'
    pension_type = factory.SubFactory(PensionTypeFactory)


@factory.django.mute_signals(signals.post_save)
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
