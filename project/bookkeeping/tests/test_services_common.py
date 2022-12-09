from decimal import Decimal

import pytest
from freezegun import freeze_time

from ..services import common as T

pytestmark = pytest.mark.django_db


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
