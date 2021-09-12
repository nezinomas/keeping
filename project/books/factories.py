from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Book, BookTarget


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    started = date(1999, 1, 1)
    author = 'Author'
    title = 'Book Title'
    remark = 'Remark'
    user = factory.SubFactory(UserFactory)


class BookTargetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookTarget

    quantity = 100
    year = 1999
    user = factory.SubFactory(UserFactory)
