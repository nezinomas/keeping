import tempfile
from datetime import date

import pytest
from django.test import override_settings
from freezegun import freeze_time
from mock import patch

from ...users.factories import UserFactory
from ..factories import CountTypeFactory
from ..forms import CountForm, CountTypeForm

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                   Count
# ---------------------------------------------------------------------------------------
def test_form_init():
    CountForm()


def test_form_init_fields():
    form = CountForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form
    assert '<input type="text" name="counter_type"' not in form


@freeze_time('1000-01-01')
def test_form_year_initial_value():
    UserFactory()

    form = CountForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert '<input type="number" name="quantity" value="1"' in form


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch('project.core.lib.utils.get_request_kwargs', return_value='xxx')
def test_form_valid_data(mck):
    CountTypeFactory(title='xxx')

    form = CountForm(data={
        'date': '1999-01-01',
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.quantity == 1.0
    assert data.user.username == 'bob'
    assert data.counter_type == 'xxx'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch('project.core.lib.utils.get_request_kwargs', return_value='xxx')
@freeze_time('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_form_invalid_date(mck, year):
    CountTypeFactory(title='xxx')

    form = CountForm(data={
        'date': f'{year}-01-01',
        'quantity': 1.0
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


def test_form_blank_data():
    form = CountForm({})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert '__all__' in form.errors
    assert 'date' in form.errors
    assert 'quantity' in form.errors


@patch('project.core.lib.utils.get_request_kwargs', return_value='xxx')
def test_form_counter_not_exist(mck):
    form = CountForm(data={
        'date': '1999-01-01',
        'quantity': 1.0
    })

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert '__all__' in form.errors
    assert 'Nėra tokio skaitiklio' in form.errors['__all__']


# ---------------------------------------------------------------------------------------
#                                                                              Count Type
# ---------------------------------------------------------------------------------------
def test_count_type_init():
    CountTypeForm()


def test_count_type_init_fields():
    form = CountTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="user"' not in form


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_count_type_valid_data():
    form = CountTypeForm(data={'title': 'XXXXX'})

    assert form.is_valid()

    data = form.save()

    assert data.user.username == 'bob'
    assert data.title == 'XXXXX'


def test_count_type_blank_data():
    form = CountTypeForm({})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'title' in form.errors