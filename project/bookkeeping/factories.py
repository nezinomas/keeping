import factory
from django.db.models.signals import post_save

from ..accounts.factories import AccountFactory
from ..savings.factories import SavingTypeFactory
from . import models


@factory.django.mute_signals(post_save)
class SavingWorthFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.SavingWorth

    saving_type = factory.SubFactory(SavingTypeFactory)
    price = 0.5


@factory.django.mute_signals(post_save)
class AccountWorthFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 0.5
