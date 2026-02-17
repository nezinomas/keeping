from datetime import date

import pytest

from ..factories import BookFactory, BookTargetFactory
from ...services.info_row import InfoRow

pytestmark = pytest.mark.django_db


def test_readed(main_user):
    BookFactory()
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 12, 31))
    BookFactory(started=date(1999, 2, 1), ended=date(1999, 12, 31))

    obj = InfoRow(main_user)
    actual = obj.readed

    assert actual == 2


def test_readed_with_no_books(main_user):
    obj = InfoRow(main_user)
    actual = obj.readed

    assert actual == 0


def test_reading(main_user):
    BookFactory()
    BookFactory()
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 1, 31))

    obj = InfoRow(main_user)
    actual = obj.reading

    assert actual == 2


def test_reading_with_no_books(main_user):
    obj = InfoRow(main_user)
    actual = obj.reading

    assert actual == 0


def test_target(main_user):
    BookTargetFactory()

    obj = InfoRow(main_user)
    actual = obj.target

    assert actual.quantity == 100


def test_target_with_no_targets(main_user):
    obj = InfoRow(main_user)
    actual = obj.target

    assert actual == 0
