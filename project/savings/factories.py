from datetime import date as dt
from datetime import datetime

import factory
import pytz
from django.db import models
from django.db.models import signals

from ..accounts.factories import AccountFactory
from ..journals.factories import JournalFactory
from .models import Saving, SavingBalance, SavingType


class SavingTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingType
        django_get_or_create = ("title",)

    title = "Savings"
    journal = factory.SubFactory(JournalFactory)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        created = kwargs.pop("created", None)

        obj = super()._create(target_class, *args, **kwargs)

        if created is not None:
            obj.created = created
        else:
            obj.created = datetime(2, 2, 2, tzinfo=pytz.utc)

        models.Model.save(obj)

        return obj


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
