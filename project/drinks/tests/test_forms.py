import pytest

from ..factories import DrinkTargetFactory
from ..forms import DrinkForm, DrinkTargetForm


def test_drink_target_init():
    DrinkTargetForm()


@pytest.mark.django_db
def test_drink_target_valid_data():
    form = DrinkTargetForm(data={
        'year': 1974,
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1974
    assert data.quantity == 1.0


@pytest.mark.django_db
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
