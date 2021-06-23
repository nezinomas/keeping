from datetime import date

from factory.django import DjangoModelFactory

from . import models


class JournalFactory(DjangoModelFactory):
    class Meta:
        model = models.Journal
        django_get_or_create = ('title', )

    title = 'bob Journal'
    first_record = date(1999, 1, 1)
