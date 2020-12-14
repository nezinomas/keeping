from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Count


class CountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Count

    date = date(1999, 1, 1)
    quantity = 1
    counter_type = 'Counter Type'
    user = factory.SubFactory(UserFactory)
