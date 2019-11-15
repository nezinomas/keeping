from datetime import date

import factory

from ..auths.factories import UserFactory
from .models import Drink, DrinkTarget


class DrinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = Drink

    date = date(1999, 1, 1)
    quantity = 1
    user = factory.SubFactory(UserFactory)


class DrinkTargetFactory(factory.DjangoModelFactory):
    class Meta:
        model = DrinkTarget

    year = 1999
    quantity = 100
    user = factory.SubFactory(UserFactory)
