from datetime import date

import freezegun
import pytest
from mock import patch

from ..factories import DrinkFactory
from ..lib import views_helper as T


@freezegun.freeze_time('1999-01-03')
@pytest.mark.django_db
@patch('project.drinks.models.DrinkQuerySet.App_name', 'Counter Type')
def test_dry_days(get_user):
    DrinkFactory()

    actual = T._dry_days(1999)

    assert actual == {'date': date(1999, 1, 1), 'delta': 2}



@pytest.mark.django_db
def test_dry_days_no_records(get_user):
    DrinkFactory()

    actual = T._dry_days(2000)

    assert actual == {}


def test_target_label_position_between():
    actual = T._target_label_position(avg=55, target=50)

    assert actual == 15


def test_target_label_position_higher():
    actual = T._target_label_position(avg=55, target=500)

    assert actual == -5


def test_target_label_position_lower():
    actual = T._target_label_position(avg=500, target=50)

    assert actual == -5


def test_avg_label_position_between():
    actual = T._avg_label_position(avg=50, target=55)

    assert actual == 15


def test_avg_label_position_higher():
    actual = T._avg_label_position(avg=55, target=500)

    assert actual == -5


def test_avg_label_position_lower():
    actual = T._avg_label_position(avg=500, target=50)

    assert actual == -5
