from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from ..journals.factories import JournalFactory
from . import models


class BorrowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Debt

    date = dt(1999, 1, 1)
    type = 'borrow'
    name = factory.Faker('first_name')
    price = Decimal('100')
    returned = Decimal('25')
    closed = False
    remark = 'Borrow Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class BorrowReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DebtReturn

    date = dt(1999, 1, 2)
    price = Decimal('5')
    remark = 'Borrow Return Remark'
    account = factory.SubFactory(AccountFactory)
    borrow = factory.SubFactory(BorrowFactory)


class LendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Debt

    date = dt(1999, 1, 1)
    type = 'lend'
    name = factory.Faker('first_name')
    price = Decimal('100')
    returned = Decimal('25')
    closed = False
    remark = 'Lend Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class LendReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DebtReturn

    date = dt(1999, 1, 2)
    price = Decimal('5')
    remark = 'Lend Return Remark'
    account = factory.SubFactory(AccountFactory)
    lent = factory.SubFactory(LendFactory)
