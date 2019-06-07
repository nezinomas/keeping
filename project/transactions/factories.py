from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from .models import Transaction


class TransactionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Transaction

    date = dt(1999, 1, 1)
    amount = Decimal(200)
    from_account = factory.SubFactory(AccountFactory)
    from_account = factory.SubFactory(AccountFactory, title='Account2')
