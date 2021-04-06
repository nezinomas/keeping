import factory

from ..accounts.factories import AccountFactory
from ..pensions.factories import PensionTypeFactory
from ..savings.factories import SavingTypeFactory
from . import models


class SavingWorthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SavingWorth

    saving_type = factory.SubFactory(SavingTypeFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted


class AccountWorthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted


class PensionWorthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PensionWorth

    pension_type = factory.SubFactory(PensionTypeFactory)
    price = 0.5

    @factory.post_generation
    def date(self, create, extracted, **kwargs):
        if extracted:
            self.date = extracted
