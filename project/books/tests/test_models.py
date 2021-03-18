from datetime import date

import pytest
from django.core.validators import ValidationError

from ...users.factories import UserFactory
from ..factories import BookFactory, BookTargetFactory
from ..models import Book, BookTarget

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
    b1 = BookFactory(title='x1')
    b2 = BookFactory(title='x2', ended=date(1999, 1, 2))
    BookFactory(started=date(2000, 1, 1))
    BookFactory(ended=date(2000, 1, 1))
    BookFactory(user=UserFactory(username='XXX'))

    actual = Book.objects.year(1999)

    assert actual.count() == 2
    assert actual[0] == b1
    assert actual[1] == b2


def test_book_fields(get_user):
    BookFactory(ended=date(1999, 1, 31))

    actual = list(Book.objects.items())[0]

    assert actual.author == 'Author'
    assert actual.title == 'Book Title'
    assert actual.remark == 'Remark'

    assert date(1999, 1, 1) == actual.started
    assert date(1999, 1, 31) == actual.ended


def test_book_readed_one_year(get_user):
    BookFactory()
    BookFactory(ended=date(1999, 1, 31))
    BookFactory(ended=date(1999, 12, 31))
    BookFactory(ended=date(1999, 12, 31), user=UserFactory(username='X'))

    actual = list(Book.objects.readed(year=1999))

    assert actual == [{'year': 1999, 'cnt': 2}]


def test_book_readed_one_year_no_data(get_user):
    actual = list(Book.objects.readed(year=1999))

    assert actual == []


def test_book_readed_all_years(get_user):
    BookFactory()
    BookFactory(ended=date(1999, 1, 31))
    BookFactory(ended=date(1999, 12, 31))
    BookFactory(ended=date(1998, 1, 31))
    BookFactory(ended=date(1998, 1, 31), user=UserFactory(username='XXX'))

    actual = list(Book.objects.readed())

    assert actual == [{'year': 1998, 'cnt': 1}, {'year': 1999, 'cnt': 2}]


def test_book_readed_all_years_no_data(get_user):
    actual = list(Book.objects.readed())

    assert actual == []


def test_book_reading(get_user):
    BookFactory()
    BookFactory(started=date(1000, 1, 1))
    BookFactory(started=date(3000, 1, 1))
    BookFactory(ended=date(2000, 1, 31))
    BookFactory(user=UserFactory(username='XXX'))

    actual = Book.objects.reading(1999)

    assert actual == {'reading': 2}



# ----------------------------------------------------------------------------
#                                                                 Book Target
# ----------------------------------------------------------------------------
def test_drink_target_str():
    actual = BookTargetFactory.build()

    assert str(actual) == '1999: 100'


def test_drink_target_related(get_user):
    BookTargetFactory()
    BookTargetFactory(user=UserFactory(username='XXX'))

    actual = BookTarget.objects.related()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_items(get_user):
    BookTargetFactory(year=1999)
    BookTargetFactory(year=2000, user=UserFactory(username='XXX'))

    actual = BookTarget.objects.items()

    assert len(actual) == 1
    assert actual[0].user.username == 'bob'


def test_drink_target_year(get_user):
    BookTargetFactory(year=1999)
    BookTargetFactory(year=1999, user=UserFactory(username='XXX'))

    actual = list(BookTarget.objects.year(1999))

    assert len(actual) == 1
    assert actual[0].year == 1999
    assert actual[0].user.username == 'bob'


def test_drink_target_year_positive():
    actual = BookTargetFactory.build(year=-2000)

    try:
        actual.full_clean()
    except ValidationError as e:
        assert 'year' in e.message_dict


@pytest.mark.xfail(raises=Exception)
def test_drink_target_year_unique():
    BookTargetFactory(year=1999)
    BookTargetFactory(year=1999)


def test_drink_target_ordering():
    BookTargetFactory(year=1970)
    BookTargetFactory(year=1999)

    actual = list(BookTarget.objects.all())

    assert str(actual[0]) == '1999: 100'
    assert str(actual[1]) == '1970: 100'
