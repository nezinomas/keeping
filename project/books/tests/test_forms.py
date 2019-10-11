from datetime import date

import pytest

from ..factories import BookFactory
from ..forms import BookForm


def test_book_init():
    BookForm()


@pytest.mark.django_db
def test_book_valid_data():
    form = BookForm(data={
        'started': '1974-01-01',
        'ended': '1974-01-31',
        'author': 'Author',
        'title': 'Title',
    })

    assert form.is_valid()

    data = form.save()

    assert data.started == date(1974, 1, 1)
    assert data.ended == date(1974, 1, 31)
    assert data.author == 'Author'
    assert data.title == 'Title'


def test_book_blank_data():
    form = BookForm(data={})

    assert not form.is_valid()

    assert 'started' in form.errors
    assert 'author' in form.errors
    assert 'title' in form.errors


def test_book_author_too_long():
    form = BookForm(data={
        'started': '1974-01-01',
        'ended': '1974-01-31',
        'author': 'Author'*250,
        'title': 'Title',
    })

    assert not form.is_valid()

    assert 'author' in form.errors


def test_book_title_too_long():
    form = BookForm(data={
        'started': '1974-01-01',
        'ended': '1974-01-31',
        'author': 'Author',
        'title': 'Title'*254,
    })

    assert not form.is_valid()

    assert 'title' in form.errors
