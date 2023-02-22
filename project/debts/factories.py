from datetime import date as dt

import factory

from ..accounts.factories import AccountFactory
from ..journals.factories import JournalFactory
from . import models


class BorrowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Debt

    date = dt(1999, 1, 1)
    debt_type = 'borrow'
    name = factory.Faker('first_name')
    price = 100
    closed = False
    remark = 'Borrow Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class BorrowReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DebtReturn

    date = dt(1999, 1, 2)
    price = 5
    remark = 'Borrow Return Remark'
    account = factory.SubFactory(AccountFactory)
    debt = factory.SubFactory(BorrowFactory)


class LendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Debt

    date = dt(1999, 1, 1)
    debt_type = 'lend'
    name = factory.Faker('first_name')
    price = 100
    closed = False
    remark = 'Lend Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class LendReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DebtReturn

    date = dt(1999, 1, 2)
    price = 6
    remark = 'Lend Return Remark'
    account = factory.SubFactory(AccountFactory)
    debt = factory.SubFactory(LendFactory)
