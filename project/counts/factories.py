from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Count, CountType


class CountTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountType
        django_get_or_create = ('title','user',)

    user = factory.SubFactory(UserFactory)
    title = 'Count Type'


class CountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Count

    user = factory.SubFactory(UserFactory)
    date = date(1999, 1, 1)
    count_type = factory.SubFactory(CountTypeFactory)
    quantity = 1
