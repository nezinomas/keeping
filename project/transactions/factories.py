from datetime import date as dt
from decimal import Decimal

import factory
from django.db.models.signals import post_save

from ..accounts.factories import AccountFactory
from ..savings.factories import SavingTypeFactory
from .models import SavingChange, SavingClose, Transaction


@factory.django.mute_signals(post_save)
class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    date = dt(1999, 1, 1)
    price = Decimal(200)
    to_account = factory.SubFactory(AccountFactory, title='Account2')
    from_account = factory.SubFactory(AccountFactory)


@factory.django.mute_signals(post_save)
class SavingChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingChange

    date = dt(1999, 1, 1)
    price = Decimal(10.0)
    fee = Decimal(0.25)
    to_account = factory.SubFactory(SavingTypeFactory, title='Savings To')
    from_account = factory.SubFactory(SavingTypeFactory, title='Savings From')


@factory.django.mute_signals(post_save)
class SavingCloseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingClose

    date = dt(1999, 1, 1)
    price = Decimal(10.0)
    fee = Decimal(0.25)
    to_account = factory.SubFactory(AccountFactory, title='Account To')
    from_account = factory.SubFactory(SavingTypeFactory, title='Savings From')
