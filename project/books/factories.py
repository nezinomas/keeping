from datetime import date

import factory

from ..users.factories import UserFactory
from .models import Book


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    started = date(1999, 1, 1)
    author = 'Author'
    title = 'Book Title'
    remark = 'Remark'
    user = factory.SubFactory(UserFactory)
