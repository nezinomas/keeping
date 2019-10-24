from datetime import date as dt
from decimal import Decimal

import factory
from django.db.models.signals import post_save

from ..accounts.factories import AccountFactory
from .models import Saving, SavingType


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
