from datetime import date

import factory

from .models import Book


class BookFactory(factory.DjangoModelFactory):
    class Meta:
        model = Book

    started = date(1999, 1, 1)
    author = 'Author'
    title = 'Book Title'
    remark = 'Remark'
