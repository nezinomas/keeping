from datetime import date

import pytest

from ..factories import BookFactory
from ..models import Book


def test_book_str():
    book = BookFactory.build()

    assert 'Book Title' == str(book)


@pytest.mark.django_db
def test_book_items():
    BookFactory()

    assert 1 == Book.objects.items().count()


@pytest.mark.django_db
def test_book_year():
    BookFactory()
    BookFactory(started=date(2000, 1, 1))

    assert 1 == Book.objects.year(1999).count()


@pytest.mark.django_db
def test_book_fields():
    BookFactory(ended=date(1999, 1, 31))

    actual = list(Book.objects.items())[0]

    assert 'Author' == actual.author
    assert 'Book Title' == actual.title
    assert 'Remark' == actual.remark

    assert date(1999, 1, 1) == actual.started
    assert date(1999, 1, 31) == actual.ended
