from datetime import date

import pytest
from freezegun import freeze_time
from mock import patch

from ...users.factories import UserFactory
from ..factories import DrinkTargetFactory
from ..forms import DrinkCompareForm, DrinkForm, DrinkTargetForm

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                                   Drink
# ---------------------------------------------------------------------------------------
def test_drink_init(get_user):
    DrinkForm()


def test_drink_init_fields(get_user):
    form = DrinkForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form
    assert '<input type="text" name="counter_type"' not in form


@freeze_time('1000-01-01')
def test_drink_year_initial_value(get_user):
    UserFactory()

    form = DrinkForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


@patch('project.drinks.forms.App_name', 'Counter Type')
def test_drink_valid_data(get_user):
    form = DrinkForm(data={
        'date': '1974-01-01',
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1974, 1, 1)
    assert data.quantity == 1.0
    assert data.user.username == 'bob'
    assert data.counter_type == 'Counter Type'


def test_drink_blank_data(get_user):
    form = DrinkForm({})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'date' in form.errors
    assert 'quantity' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                            Drink Target
# ---------------------------------------------------------------------------------------
def test_drink_target_init(get_user):
    DrinkTargetForm()


def test_drink_target_init_fields(get_user):
    form = DrinkTargetForm().as_p()

    assert '<input type="text" name="year"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form


@freeze_time('1000-01-01')
def test_drink_target_year_initial_value(get_user):
    UserFactory()

    form = DrinkTargetForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_drink_target_valid_data(get_user):
    form = DrinkTargetForm(data={
        'year': 1974,
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1974
    assert data.quantity == 1.0
    assert data.user.username == 'bob'


def test_drink_target_year_validation(get_user):
    DrinkTargetFactory()

    form = DrinkTargetForm(data={
        'year': 1999,
        'quantity': 200
    })

    assert not form.is_valid()

    assert 'year' in form.errors


def test_drink_target_blank_data(get_user):
    form = DrinkTargetForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'quantity' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                            Drink Filter
# ---------------------------------------------------------------------------------------
def test_drink_filter_init(get_user):
    DrinkCompareForm()


def test_drink_filter_init_fields(get_user):
    form = DrinkCompareForm().as_p()

    assert '<input type="number" name="year1"' in form
    assert '<input type="number" name="year2"' in form


@freeze_time('1999-01-01')
def test_drink_filter_initial_values(get_user):
    form = DrinkCompareForm().as_p()

    assert '<input type="number" name="year2" value="1999"' in form


@pytest.mark.parametrize(
    'year1, year2',
    [
        (None, None),
        ('', ''),
        (None, 1111),
        ('', 1111),
        (1111, None),
        (1111, ''),
        (111, 111),
        (11111, 11111),
        ('xxx', 'xxx'),
    ]
)
def test_drink_filter_form_invalid(year1, year2):
    form = DrinkCompareForm(
        data={
            'year1': year1,
            'year2': year2,
        }
    )

    assert not form.is_valid()


@pytest.mark.parametrize(
    'year1, year2',
    [
        (1111, 1111),
        (1111, 9999),
    ]
)
def test_drink_filter_form_valid(year1, year2):
    form = DrinkCompareForm(
        data={
            'year1': year1,
            'year2': year2,
        }
    )

    assert form.is_valid()
