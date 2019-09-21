from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from .models import SavingChange, SavingClose, Transaction


class TransactionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Transaction

    date = dt(1999, 1, 1)
    price = Decimal(200)
    to_account = factory.SubFactory(AccountFactory, title='Account2')
    from_account = factory.SubFactory(AccountFactory)


class SavingChangeFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavingChange


class SavingCloseFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavingClose
