from datetime import date
from decimal import Decimal

import pytest

from ..models import Expense as T

pytestmark = pytest.mark.django_db


def test_sums_months(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'ex': Decimal(1.75)},
    ]

    actual = list(T.objects.expense_sum(1999, 'ex'))

    assert expect == actual
