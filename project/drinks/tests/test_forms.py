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
def test_drink_init():
    DrinkForm()


def test_drink_init_fields():
    form = DrinkForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form
    assert '<input type="text" name="counter_type"' not in form


def test_drink_help_text():
    form = DrinkForm().as_p()

    assert f'Įvedus daugiau nei 20, kiekis bus konvertuotas į mL.' in form


@freeze_time('1000-01-01')
def test_drink_year_initial_value():
    UserFactory()

    form = DrinkForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


@patch('project.drinks.forms.App_name', 'Counter Type')
def test_drink_valid_data():
    form = DrinkForm(data={
        'date': '1999-01-01',
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.quantity == 1.0
    assert data.user.username == 'bob'
    assert data.counter_type == 'Counter Type'


@patch('project.drinks.forms.App_name', 'Counter Type')
@freeze_time('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_drink_invalid_date(year):
    form = DrinkForm(data={
        'date': f'{year}-01-01',
        'quantity': 1.0
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


def test_drink_blank_data():
    form = DrinkForm({})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'date' in form.errors
    assert 'quantity' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                            Drink Target
# ---------------------------------------------------------------------------------------
def test_drink_target_init():
    DrinkTargetForm()


def test_drink_target_init_fields():
    form = DrinkTargetForm().as_p()

    assert '<input type="text" name="year"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form


@freeze_time('1000-01-01')
def test_drink_target_year_initial_value():
    UserFactory()

    form = DrinkTargetForm().as_p()

    assert '<input type="text" name="year" value="1999"' in form


def test_drink_target_valid_data():
    form = DrinkTargetForm(data={
        'year': 1974,
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1974
    assert data.quantity == 1.0
    assert data.user.username == 'bob'


def test_drink_target_year_validation():
    DrinkTargetFactory()

    form = DrinkTargetForm(data={
        'year': 1999,
        'quantity': 200
    })

    assert not form.is_valid()

    assert 'year' in form.errors


def test_drink_target_blank_data():
    form = DrinkTargetForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'year' in form.errors
    assert 'quantity' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                            Drink Filter
# ---------------------------------------------------------------------------------------
def test_drink_filter_init():
    DrinkCompareForm()


def test_drink_filter_init_fields():
    form = DrinkCompareForm().as_p()

    assert '<input type="number" name="year1"' in form
    assert '<input type="number" name="year2"' in form


@freeze_time('1999-01-01')
def test_drink_filter_initial_values():
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
