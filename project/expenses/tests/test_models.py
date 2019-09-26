from datetime import date
from decimal import Decimal

import pytest

from ..models import Expense as T

pytestmark = pytest.mark.django_db


def test_sums_months(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5)},
        {'date': date(1999, 12, 1), 'sum': Decimal(1.25)},
    ]

    actual = [*T.objects.month_expense(1999)]

    assert expect == actual


def test_month_expense_type(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 12, 1), 'sum': Decimal(1.25), 'title': 'Expense Type'},
    ]

    actual = [*T.objects.month_expense_type(1999)]

    assert expect == actual


def test_sums_months_one_month(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5)},
    ]

    actual = [*T.objects.month_expense(1999, 1)]

    assert expect == actual


def test_month_expense_type_one_month(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
    ]

    actual = [*T.objects.month_expense_type(1999, 1)]

    assert expect == actual


def test_day_expense_type(expenses_january):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 1, 11), 'sum': Decimal(0.5), 'title': 'Expense Type'},
    ]

    actual = [*T.objects.day_expense_type(1999, 1)]

    assert expect == actual
