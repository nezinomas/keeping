from datetime import date as dt
from decimal import Decimal

import factory
from django.db.models.signals import post_save
from .models import Pension, PensionType


@factory.django.mute_signals(post_save)
class PensionTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PensionType
        django_get_or_create = ('title',)

    title = 'PensionType'


@factory.django.mute_signals(post_save)
class PensionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Pension

    date = dt(1999, 1, 1)
    price = Decimal(100)
    remark = 'remark'
    pension_type = factory.SubFactory(PensionTypeFactory)
