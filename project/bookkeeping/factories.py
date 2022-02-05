import factory
from factory.django import DjangoModelFactory

from ..accounts.factories import AccountFactory
from ..pensions.factories import PensionTypeFactory
from ..savings.factories import SavingTypeFactory
from . import models


class SavingWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.SavingWorth

    saving_type = factory.SubFactory(SavingTypeFactory)
    price = 0.5


class AccountWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 0.5


class PensionWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.PensionWorth

    pension_type = factory.SubFactory(PensionTypeFactory)
    price = 0.5
