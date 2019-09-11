import pytest
from decimal import Decimal
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..models import Income as T

pytestmark = pytest.mark.django_db


def test_sums_months(incomes):
    expect = [
        {'month': 1, 'incomes': Decimal(5.5)},
        {'month': 2, 'incomes': Decimal(1.25)},
    ]

    actual = list(T.objects.sum_by_month(1999, 'incomes'))

    assert expect == actual


def test_sums_months_ordering(incomes):
    expect = [
        {'month': 1, 'incomes': Decimal(5.5)},
        {'month': 2, 'incomes': Decimal(1.25)},
    ]

    actual = list(T.objects.sum_by_month(1999, 'incomes'))

    assert expect[0]['month'] == 1
    assert expect[1]['month'] == 2
