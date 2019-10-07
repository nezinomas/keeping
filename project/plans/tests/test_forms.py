import pytest
from freezegun import freeze_time

from ..forms import NecessaryPlanForm
from ..models import NecessaryPlan


def test_necessary_init():
    NecessaryPlanForm()


@pytest.mark.django_db
def test_necessary_valid_data():
    form = NecessaryPlanForm(data={
        'year': 1999,
        'title': 'X',
        'january': 15.0,
    })

    assert form.is_valid()

    data = form.save()

    assert data.year == 1999
    assert data.title == 'X'
    assert data.january == 15.0
    assert not data.february


@freeze_time('1999-01-01')
def test_blank_data():
    form = NecessaryPlanForm(data={})

    assert not form.is_valid()

    assert form.errors == {
        'year': ['Šis laukas yra privalomas.'],
        'title': ['Šis laukas yra privalomas.'],
    }
