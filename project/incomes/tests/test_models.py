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

    actual = list(T.objects.income_sum(1999))

    assert expect == actual


def test_sums_months_ordering(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'incomes': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'incomes': Decimal(1.25)},
    ]

    actual = list(T.objects.income_sum(1999))

    assert expect[0]['date'] == date(1999, 1, 1)
    assert expect[1]['date'] == date(1999, 2, 1)


def test_sums_months_by_one_month(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'incomes': Decimal(5.5)}
    ]

    actual = list(T.objects.income_sum(1999, 1))

    assert 1 == len(expect)
    assert expect == actual
