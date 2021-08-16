from datetime import date

import freezegun
import pytest
from mock import patch

from ..factories import DrinkFactory
from ..lib import views_helper as T

pytestmark = pytest.mark.django_db

@freezegun.freeze_time('1999-01-03')
@patch('project.drinks.managers.DrinkQuerySet.counter_type', 'Counter Type')
def test_dry_days(fake_request):
    DrinkFactory()

    actual = T.RenderContext(fake_request)._dry_days()

    assert actual == {'date': date(1999, 1, 1), 'delta': 2}


def test_dry_days_no_records(fake_request):
    DrinkFactory()

    actual = T.RenderContext(fake_request)._dry_days()

    assert actual == {}


def test_target_label_position_between(fake_request):
    actual = T.RenderContext(fake_request)._target_label_position(avg=55, target=50)

    assert actual == 15


def test_target_label_position_higher(fake_request):
    actual = T.RenderContext(fake_request)._target_label_position(avg=55, target=500)

    assert actual == -5


def test_target_label_position_lower(fake_request):
    actual = T.RenderContext(fake_request)._target_label_position(avg=500, target=50)

    assert actual == -5


def test_avg_label_position_between(fake_request):
    actual = T.RenderContext(fake_request)._avg_label_position(avg=50, target=55)

    assert actual == 15


def test_avg_label_position_higher(fake_request):
    actual = T.RenderContext(fake_request)._avg_label_position(avg=55, target=500)

    assert actual == -5


def test_avg_label_position_lower(fake_request):
    actual = T.RenderContext(fake_request)._avg_label_position(avg=500, target=50)

    assert actual == -5
