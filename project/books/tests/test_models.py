from datetime import date

import pytest

from ..factories import BookFactory
from ..models import Book

pytestmark = pytest.mark.django_db


def test_book_str():
    book = BookFactory.build()

    assert str(book) == 'Book Title'


def test_book_items():
    BookFactory()

    assert Book.objects.items().count() == 1


def test_book_year():
    BookFactory()
    BookFactory(started=date(2000, 1, 1))

    assert Book.objects.year(1999).count() == 1


def test_book_fields():
    BookFactory(ended=date(1999, 1, 31))

    actual = list(Book.objects.items())[0]

    assert actual.author == 'Author'
    assert actual.title == 'Book Title'
    assert actual.remark == 'Remark'

    assert date(1999, 1, 1) == actual.started
    assert date(1999, 1, 31) == actual.ended
