from datetime import date as dt
from decimal import Decimal

import factory

from ..accounts.factories import AccountFactory
from ..journals.factories import JournalFactory
from . import models


class DebtFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Debt

    date = dt(1999, 1, 1)
    name = factory.Faker('first_name')
    price = Decimal('100')
    returned = Decimal('25')
    closed = False
    remark = 'Debt Remark'
    account = factory.SubFactory(AccountFactory)
    journal = factory.SubFactory(JournalFactory)


class DebtReturnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DebtReturn

    date = dt(1999, 1, 2)
    price = Decimal('5')
    remark = 'Debt Return Remark'
    account = factory.SubFactory(AccountFactory)
    debt = factory.SubFactory(DebtFactory)
