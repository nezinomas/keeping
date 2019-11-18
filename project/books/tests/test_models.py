from datetime import date

import pytest

from ...auths.factories import UserFactory
from ..factories import BookFactory
from ..models import Book

pytestmark = pytest.mark.django_db


def test_book_str():
    book = BookFactory.build()

    assert str(book) == 'Book Title'

def test_book_related(get_user):
    BookFactory()
    BookFactory(title='B1', user=UserFactory(username='XXX'))

    actual = Book.objects.related()

    assert len(actual) == 1
    assert actual[0].title == 'Book Title'


def test_book_items(get_user):
    BookFactory()
    BookFactory(title='B1', user=UserFactory(username='XXX'))

    assert Book.objects.items().count() == 1


def test_book_year(get_user):
    BookFactory()
    BookFactory(user=UserFactory(username='XXX'))
    BookFactory(started=date(2000, 1, 1))

    assert Book.objects.year(1999).count() == 1


def test_book_fields(get_user):
    BookFactory(ended=date(1999, 1, 31))

    actual = list(Book.objects.items())[0]

    assert actual.author == 'Author'
    assert actual.title == 'Book Title'
    assert actual.remark == 'Remark'

    assert date(1999, 1, 1) == actual.started
    assert date(1999, 1, 31) == actual.ended
