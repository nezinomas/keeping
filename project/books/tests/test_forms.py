from datetime import date

import pytest

from ..forms import BookForm


def test_book_init():
    BookForm()


def test_book_init_fields():
    form = BookForm().as_p()

    assert '<input type="text" name="started"' in form
    assert '<input type="text" name="ended"' in form
    assert '<input type="text" name="author"' in form
    assert '<input type="text" name="title"' in form

    assert '<select name="user"' not in form


@pytest.mark.django_db
def test_book_valid_data(get_user):
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
    assert data.user.username == 'bob'


def test_book_blank_data():
    form = BookForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
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


def test_book_author_too_short():
    form = BookForm(data={
        'started': '1974-01-01',
        'ended': '1974-01-31',
        'author': 'AA',
        'title': 'Title',
    })

    assert not form.is_valid()

    assert 'author' in form.errors


def test_book_title_too_short():
    form = BookForm(data={
        'started': '1974-01-01',
        'ended': '1974-01-31',
        'author': 'Author',
        'title': 'TT',
    })

    assert not form.is_valid()

    assert 'title' in form.errors
