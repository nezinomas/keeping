from datetime import date

import pytest

from ..factories import BookFactory, BookTargetFactory
from ..lib import views_helper as T

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _books():
    BookFactory(started=date(1974, 1, 1), ended=date(1974, 1, 2))
    BookFactory(started=date(1975, 1, 1), ended=date(1975, 1, 2))
    BookFactory(started=date(1999, 1, 1), ended=date(1999, 1, 2))
    BookFactory(started=date(1999, 2, 1), ended=date(1999, 2, 2))

    BookTargetFactory(year=1975, quantity=20)
    BookTargetFactory()


def test_chart_readed_books_categories(fake_request):
    actual = T.BookRenderer(fake_request).context_chart_readed_books()
    expect = [1974, 1975, 1999]

    assert actual['categories'] == expect


def test_chart_readed_books_targets(fake_request):
    actual = T.BookRenderer(fake_request).context_chart_readed_books()
    expect = [0, 20, 100]

    assert actual['targets'] == expect


def test_chart_readed_books_data(fake_request):
    actual = T.BookRenderer(fake_request).context_chart_readed_books()
    expect = [
        {'y': 1, 'target': 0},
        {'y': 1, 'target': 20},
        {'y': 2, 'target': 100},
    ]

    assert actual['data'] == expect
