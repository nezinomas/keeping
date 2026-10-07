from datetime import date

import factory
from django.conf import settings
from factory.django import DjangoModelFactory

from .. import models


class JournalFactory(DjangoModelFactory):
    class Meta:
        model = models.Journal
        django_get_or_create = ("title",)

    title = "bob Journal"
    first_record = date(1999, 1, 1)
    lang = factory.LazyFunction(lambda: settings.LANGUAGE_CODE)
