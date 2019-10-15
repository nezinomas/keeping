from datetime import date
from decimal import Decimal

import pytest

from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ..factories import IncomeFactory, IncomeTypeFactory
from ..models import Income, IncomeType

pytestmark = pytest.mark.django_db


def test_sum_all_months(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]

    actual = list(Income.objects.income_sum(1999))

    assert expect == actual


def test_sum_all_months_ordering(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]

    actual = list(Income.objects.income_sum(1999))

    assert expect[0]['date'] == date(1999, 1, 1)
    assert expect[1]['date'] == date(1999, 2, 1)


def test_sum_one_month(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)}
    ]

    actual = list(Income.objects.income_sum(1999, 1))

    assert 1 == len(expect)
    assert expect == actual


def test_incomes_items():
    IncomeFactory()

    assert 1 == len(Income.objects.items())


def test_incomes_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Income.objects.items()]


def test_incomes_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Income.objects.year(1999)]


def test_incomes_income_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Income.objects.income_sum(1999)]


def test_income_str():
    i = IncomeFactory.build()

    assert '1999-01-01: Income Type' == str(i)


def test_income_type_str():
    i = IncomeTypeFactory.build()

    assert 'Income Type' == str(i)


def test_summary(incomes):
    expect = [{
        'title': 'Account1',
        'i_past': Decimal(5.25),
        'i_now': Decimal(3.25),

    }, {
        'title': 'Account2',
        'i_past': Decimal(4.5),
        'i_now': Decimal(3.5),
    }]

    actual = list(Income.objects.summary(1999))

    assert_(expect, actual)
