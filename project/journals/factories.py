from datetime import date

import factory
from factory.django import DjangoModelFactory

from ..users.factories import UserFactory
from . import models


class JournalFactory(DjangoModelFactory):
    class Meta:
        model = models.Journal
        django_get_or_create = ('user', )

    user = factory.SubFactory(UserFactory)
    year = 1999
    month = 12
    first_record = date(1999, 1, 1)
