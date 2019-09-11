from datetime import date
from decimal import Decimal

import pytest

from ..models import Income as T

pytestmark = pytest.mark.django_db


def test_sums_months(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'incomes': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'incomes': Decimal(1.25)},
    ]

    actual = list(T.objects.sum_by_month(1999, 'incomes'))

    assert expect == actual


def test_sums_months_ordering(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'incomes': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'incomes': Decimal(1.25)},
    ]

    actual = list(T.objects.sum_by_month(1999, 'incomes'))

    assert expect[0]['date'] == date(1999, 1, 1)
    assert expect[1]['date'] == date(1999, 2, 1)
