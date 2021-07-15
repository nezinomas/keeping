from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from ..journals.factories import JournalFactory
from . import models


class BorrowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Borrow

    date = dt(1999, 1, 1)
    name = factory.Faker('first_name')
    price = Decimal('100')
    returned = Decimal('25')
    closed = False
    remark = 'Borrow Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class BorrowReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BorrowReturn

    date = dt(1999, 1, 2)
    price = Decimal('5')
    remark = 'Borrow Return Remark'
    account = factory.SubFactory(AccountFactory)
    borrow = factory.SubFactory(BorrowFactory)


class LentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Lent

    date = dt(1999, 1, 1)
    name = factory.Faker('first_name')
    price = Decimal('100')
    returned = Decimal('25')
    closed = False
    remark = 'Lent Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class LentReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.LentReturn

    date = dt(1999, 1, 2)
    price = Decimal('5')
    remark = 'Lent Return Remark'
    account = factory.SubFactory(AccountFactory)
    lent = factory.SubFactory(LentFactory)
