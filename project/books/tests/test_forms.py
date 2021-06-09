from datetime import date

import pytest
from freezegun import freeze_time

from ...users.factories import UserFactory
from ..factories import BookTargetFactory
from ..forms import BookForm, BookTargetForm

pytestmark = pytest.mark.django_db


def test_book_init():
    BookForm()


def test_book_init_fields():
    form = BookForm().as_p()

    assert '<input type="text" name="started"' in form
    assert '<input type="text" name="ended"' in form
    assert '<input type="text" name="author"' in form
    assert '<input type="text" name="title"' in form

    assert '<select name="user"' not in form


@freeze_time('1000-01-01')
def test_book_year_initial_value():
    UserFactory()

    form = BookForm().as_p()

    assert '<input type="text" name="started" value="1999-01-01"' in form


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
        'title': 'T',
    })

    assert not form.is_valid()

    assert 'title' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                            Book Target
# ---------------------------------------------------------------------------------------
def test_book_target_init():
    BookTargetForm()


def test_book_target_init_fields():
    form = BookTargetForm().as_p()

    assert '<input type="text" name="year"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form


@freeze_time('1000-01-01')
def test_book_target_year_initial_value():
    UserFactory()

    form = BookTargetForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_book_target_valid_data():
    form = BookTargetForm(data={
        'year': 1974,
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1974
    assert data.quantity == 1.0
    assert data.user.username == 'bob'


def test_book_target_year_validation():
    BookTargetFactory()

    form = BookTargetForm(data={
        'year': 1999,
        'quantity': 200
    })

    assert not form.is_valid()

    assert 'year' in form.errors


def test_book_target_blank_data():
    form = BookTargetForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'quantity' in form.errors
