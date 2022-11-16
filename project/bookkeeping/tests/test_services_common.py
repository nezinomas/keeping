from decimal import Decimal

import pytest
from freezegun import freeze_time

from ..services import common as T

pytestmark = pytest.mark.django_db


def test_add_latest_check_key_date_found():
    worth_data = [{'title': 'x', 'latest_check': 'a'}]
    balance_data = [{'title': 'x'}]

    actual = T.add_latest_check_key(worth_data, balance_data)

    assert actual == [{'title': 'x', 'latest_check': 'a'}]


def test_add_latest_check_key_date_not_found():
    worth_data = [{'title': 'z', 'latest_check': 'a'}]
    balance_data = [{'title': 'x'}]

    actual = T.add_latest_check_key(worth_data, balance_data)

    assert actual == [{'title': 'x', 'latest_check': None}]


@freeze_time('2000-2-5')
def test_average_current_year():
    qs = [{'year': 2000, 'sum': Decimal('12')}]

    actual = T.average(qs)

    assert actual == [6.0]


@freeze_time('2001-2-5')
def test_average_past_year():
    qs = [{'year': 2000, 'sum': Decimal('12')}]

    actual = T.average(qs)

    assert actual == [1.0]


@freeze_time('2000-2-5')
def test_average():
    qs = [
        {'year': 1999, 'sum': Decimal('12')},
        {'year': 2000, 'sum': Decimal('12')}
    ]

    actual = T.average(qs)

    assert actual == [1.0, 6.0]
