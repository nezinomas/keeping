from datetime import date

import pytest
from freezegun import freeze_time
from mock import patch

from ...users.factories import UserFactory
from ..apps import App_name
from ..forms import NightForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                       Nights
# ----------------------------------------------------------------------------
def test_night_init(get_user):
    NightForm()


def test_night_init_fields(get_user):
    form = NightForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="quantity"' in form
    assert '<select name="user"' not in form
    assert '<input type="text" name="counter_type"' not in form


@freeze_time('1000-01-01')
def test_night_year_initial_value(get_user):
    UserFactory()

    form = NightForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form
    assert '<input type="number" name="quantity" value="1"' in form


@patch(f'project.{App_name}.forms.App_name', 'Counter Type')
def test_night_valid_data(get_user):
    form = NightForm(data={
        'date': '1974-01-01',
        'quantity': 1.0
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1974, 1, 1)
    assert data.quantity == 1.0
    assert data.user.username == 'bob'
    assert data.counter_type == 'Counter Type'


def test_night_blank_data(get_user):
    form = NightForm({})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'date' in form.errors
    assert 'quantity' in form.errors
