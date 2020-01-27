from datetime import date

import pytest
from freezegun import freeze_time

from ...users.factories import UserFactory
from ..factories import DrinkTargetFactory
from ..forms import DrinkForm, DrinkTargetForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                        Drink
# ----------------------------------------------------------------------------
def test_drink_init(get_user):
    DrinkForm()


def test_drink_init_fields(get_user):
    form = DrinkForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form


@freeze_time('1000-01-01')
def test_drink_year_initial_value(get_user):
    UserFactory()

    form = DrinkForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


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


def test_drink_blank_data(get_user):
    form = DrinkForm({})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'date' in form.errors
    assert 'quantity' in form.errors


# ----------------------------------------------------------------------------
#                                                                 Drink Target
# ----------------------------------------------------------------------------
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
