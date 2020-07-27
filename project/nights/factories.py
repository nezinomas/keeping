from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Night


class NightFactory(factory.DjangoModelFactory):
    class Meta:
        model = Night

    date = date(1999, 1, 1)
    quantity = 1
    counter_type = 'Counter Type'
    user = factory.SubFactory(UserFactory)
