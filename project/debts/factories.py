from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from ..users.factories import UserFactory
from . import models


class BorrowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Borrow

    date = dt(1999, 1, 1)
    name = 'Name'
    price = Decimal('100')
    returned = Decimal('25')
    closed = False
    account = factory.SubFactory(AccountFactory)
    user = factory.SubFactory(UserFactory)
