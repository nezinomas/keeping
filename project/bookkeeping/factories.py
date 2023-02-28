from datetime import datetime
from zoneinfo import ZoneInfo

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
    price = 5
    date = datetime(1999, 1, 1, 2, 3, 4, tzinfo=ZoneInfo("Europe/Vilnius"))


class AccountWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.AccountWorth

    account = factory.SubFactory(AccountFactory)
    price = 5
    date = datetime(1999, 1, 1, 2, 3, 4, tzinfo=ZoneInfo("Europe/Vilnius"))


class PensionWorthFactory(DjangoModelFactory):
    class Meta:
        model = models.PensionWorth

    pension_type = factory.SubFactory(PensionTypeFactory)
    price = 5
    date = datetime(1999, 1, 1, 2, 3, 4, tzinfo=ZoneInfo("Europe/Vilnius"))
