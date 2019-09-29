from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...expenses.factories import ExpenseFactory
from ..models import Expense as T

pytestmark = pytest.mark.django_db


@pytest.fixture()
def expenses_more():
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=0.30,
        account=AccountFactory(title='Account1'),
        exception=True
    )


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


def test_month_exception_sum(expenses_january, expenses_more):
    actual = [*T.objects.month_exceptions(1999, 1)]

    assert date(1999, 1, 1) == actual[0]['date']
    assert 'Expense Type' == actual[0]['title']
    assert round(Decimal(0.55), 2) == round(actual[0]['sum'], 2)
