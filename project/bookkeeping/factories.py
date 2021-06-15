from datetime import date

import factory
from factory.django import DjangoModelFactory

from ..accounts.factories import AccountFactory
from ..pensions.factories import PensionTypeFactory
from ..savings.factories import SavingTypeFactory
from ..users.factories import UserFactory
from . import models


class BookkeepingFactory(DjangoModelFactory):
    class Meta:
        model = models.Bookkeeping
        django_get_or_create = ('user', )

    user = factory.SubFactory(UserFactory)
    year = 1999
    month = 12
    first_record = date(1999, 1, 1)


class SavingWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.SavingWorth

    saving_type = factory.SubFactory(SavingTypeFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted


class AccountWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted


class PensionWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.PensionWorth

    pension_type = factory.SubFactory(PensionTypeFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted
