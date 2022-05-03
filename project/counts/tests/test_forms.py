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
    assert '<select name="count_type"' in form


@freeze_time('1000-01-01')
def test_form_year_initial_value():
    UserFactory()

    form = CountForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert '<input type="number" name="quantity" value="1"' in form


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_form_valid_data():
    obj = CountTypeFactory(title='Xxx')

    form = CountForm(data={
        'date': '1999-01-01',
        'count_type': obj,
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.quantity == 1.0
    assert data.user.username == 'bob'
    assert data.count_type.title == 'Xxx'
    assert data.count_type.slug == 'xxx'


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@freeze_time('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_form_invalid_date(year):
    obj = CountTypeFactory(title='xxx')

    form = CountForm(data={
        'date': f'{year}-01-01',
        'count_type': obj,
        'quantity': 1.0
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


def test_form_blank_data():
    form = CountForm({})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert 'date' in form.errors
    assert 'quantity' in form.errors
    assert 'count_type' in form.errors


def test_form_no_count_type():
    form = CountForm(data={
        'date': '1999-01-01',
        'quantity': 1.0
    })

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert 'count_type' in form.errors
    assert 'Šis laukas yra privalomas.' in form.errors['count_type']


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


@pytest.mark.parametrize(
    'reserved_title',
    [
        ('none'),
        ('None'),
        ('type'),
        ('Type'),
        ('update'),
        ('Update'),
        ('delete'),
        ('Delete'),
    ]
)
def test_count_type_reserved_title(reserved_title):
    form = CountTypeForm(data={'title': reserved_title})

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert 'title' in form.errors
    assert 'Šis pavadinimas rezervuotas sistemai.' in form.errors['title']


def test_form_count_type_and_second_user(main_user, second_user):
    CountTypeFactory(title='T1', user=main_user)
    CountTypeFactory(title='T2', user=second_user)

    form = CountForm({}).as_p()

    assert '<option value="1">T1</option>' in form
    assert '<option value="2">T2</option>' not in form


@patch('project.core.lib.utils.get_request_kwargs', return_value='t1')
def test_form_load_select_count_type(mck):
    CountTypeFactory(title='T1')
    CountTypeFactory(title='T2')

    form = CountForm().as_p()

    assert '<option value="1" selected>T1</option>' in form
