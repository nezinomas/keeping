from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Counter, CounterType


class CounterTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = CounterType
        django_get_or_create = ('title',)

    title = 'Counter Type'
    user = factory.SubFactory(UserFactory)


class CounterFactory(factory.DjangoModelFactory):
    class Meta:
        model = Counter

    date = date(1999, 1, 1)
    quantity = 1
    counter_type = factory.SubFactory(CounterTypeFactory)
