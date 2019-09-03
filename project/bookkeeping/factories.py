import factory

from ..accounts.factories import AccountFactory
from ..savings.factories import SavingTypeFactory
from . import models


class SavingWorthFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.SavingWorth

    saving_type = factory.SubFactory(SavingTypeFactory)
    price = 0.5


class AccountWorthFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 0.5
