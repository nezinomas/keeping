from datetime import date as dt
from decimal import Decimal

import factory
from django.db.models.signals import post_save

from ..accounts.factories import AccountFactory
from ..users.factories import UserFactory
from .models import Income, IncomeType


@factory.django.mute_signals(post_save)
class IncomeTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = IncomeType
        django_get_or_create = ('title',)

    title = 'Income Type'
    user = factory.SubFactory(UserFactory)


@factory.django.mute_signals(post_save)
class IncomeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Income

    date = dt(1999, 1, 1)
    price = Decimal(1000.62)
    remark = 'remark'
    account = factory.SubFactory(AccountFactory)
    income_type = factory.SubFactory(IncomeTypeFactory)
