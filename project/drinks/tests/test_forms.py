from datetime import date

import pytest

from ..factories import DrinkTargetFactory
from ..forms import DrinkForm, DrinkTargetForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                        Drink
# ----------------------------------------------------------------------------
def test_drink_init():
    DrinkForm()


def test_drink_valid_data():
    form = DrinkForm(data={
        'date': '1974-01-01',
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1974, 1, 1)
    assert data.quantity == 1.0


def test_drink_blank_data():
    form = DrinkForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'quantity' in form.errors


# ----------------------------------------------------------------------------
#                                                                 Drink Target
# ----------------------------------------------------------------------------
def test_drink_target_init():
    DrinkTargetForm()


def test_drink_target_valid_data():
    form = DrinkTargetForm(data={
        'year': 1974,
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1974
    assert data.quantity == 1.0


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

    assert 'year' in form.errors
    assert 'quantity' in form.errors
