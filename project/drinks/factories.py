from datetime import date

import factory

from .models import Drink


class DrinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = Drink

    date = date(1999, 1, 1)
    quantity = 1
