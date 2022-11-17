from datetime import date

import pytest

from ..factories import BookFactory, BookTargetFactory
from ..services.info_row import InfoRow

pytestmark = pytest.mark.django_db


def test_readed():
    BookFactory()
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 12, 31))
    BookFactory(started=date(1999, 2, 1), ended=date(1999, 12, 31))

    obj = InfoRow(year=1999)
    actual = obj.readed

    assert actual == 2


def test_readed_with_no_books():
    obj = InfoRow(year=1999)
    actual = obj.readed

    assert actual == 0


def test_reading():
    BookFactory()
    BookFactory()
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 1, 31))

    obj = InfoRow(year=1999)
    actual = obj.reading

    assert actual == 2


def test_reading_with_no_books():
    obj = InfoRow(year=1999)
    actual = obj.reading

    assert actual == 0


def test_target():
    BookTargetFactory()

    obj = InfoRow(year=1999)
    actual = obj.target

    assert actual.quantity == 100


def test_target_with_no_targets():
    obj = InfoRow(year=1999)
    actual = obj.target

    assert actual == 0
