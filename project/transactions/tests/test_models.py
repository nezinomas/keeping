from datetime import date
from decimal import Decimal

import pytest

from ..models import SavingClose

pytestmark = pytest.mark.django_db


def test_month_sums(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.month_sum(1999))

    assert expect == actual


def test_month_sums_only_january(savings_close):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(0.25)}]

    actual = list(SavingClose.objects.month_sum(1999, 1))

    assert expect == actual
