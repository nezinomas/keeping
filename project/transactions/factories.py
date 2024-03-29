from datetime import date as dt

import factory

from ..accounts.factories import AccountFactory
from ..savings.factories import SavingTypeFactory
from .models import SavingChange, SavingClose, Transaction


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    date = dt(1999, 1, 1)
    price = 200
    to_account = factory.SubFactory(AccountFactory, title="Account2")
    from_account = factory.SubFactory(AccountFactory)


class SavingChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingChange

    date = dt(1999, 1, 1)
    price = 10
    fee = 2
    to_account = factory.SubFactory(SavingTypeFactory, title="Savings To")
    from_account = factory.SubFactory(SavingTypeFactory, title="Savings From")


class SavingCloseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SavingClose

    date = dt(1999, 1, 1)
    price = 10
    fee = 2
    to_account = factory.SubFactory(AccountFactory, title="Account To")
    from_account = factory.SubFactory(SavingTypeFactory, title="Savings From")
