from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Drink, DrinkTarget


class DrinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Drink

    date = date(1999, 1, 1)
    quantity = 1
    option = 'beer'
    user = factory.SubFactory(UserFactory)


class DrinkTargetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DrinkTarget

    quantity = 100
    year = 1999
    user = factory.SubFactory(UserFactory)
