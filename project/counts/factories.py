from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Count, CountType


class CountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Count

    date = date(1999, 1, 1)
    quantity = 1
    count_type = factory.SubFactory(CountType)
    user = factory.SubFactory(UserFactory)


class CountTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountType

    user = factory.SubFactory(UserFactory)
    title = 'Count Type'
