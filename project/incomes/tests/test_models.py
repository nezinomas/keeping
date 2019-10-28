from datetime import date
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory, AccountBalanceFactory
from ...accounts.models import AccountBalance
from ...bookkeeping.factories import AccountWorthFactory
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
        'id': 1,
        'title': 'Account1',
        'i_past': Decimal(5.25),
        'i_now': Decimal(3.25),

    }, {
        'id': 2,
        'title': 'Account2',
        'i_past': Decimal(4.5),
        'i_now': Decimal(3.5),
    }]

    actual = list(Income.objects.summary(1999).order_by('account__title'))

    assert expect == actual


# ----------------------------------------------------------------------------
#                                                             post_save signal
# ----------------------------------------------------------------------------
def test_post_save_account_balace_insert(mock_crequest):
    AccountWorthFactory()
    account = AccountFactory()
    income_type = IncomeTypeFactory()

    income = Income(
        date=date(1999, 1, 1),
        price=Decimal(1),
        account=account,
        income_type=income_type
    )

    income.save()

    actual = AccountBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = actual[0]

    assert 'Account1' == actual['title']
    assert 0.0 == actual['past']
    assert 1.0 == actual['incomes']
    assert 0.0 == actual['expenses']
    assert 1.0 == actual['balance']
    assert 0.5 == actual['have']
    assert -0.5 == actual['delta']


def test_post_save_account_balace_update(mock_crequest):
    AccountBalanceFactory()
    AccountWorthFactory()
    account = AccountFactory()
    income_type = IncomeTypeFactory()

    income = Income(
        date=date(1999, 1, 1),
        price=Decimal(1),
        account=account,
        income_type=income_type
    )
    income.save()

    actual = AccountBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = actual[0]

    assert 'Account1' == actual['title']
    assert 0.0 == actual['past']
    assert 1.0 == actual['incomes']
    assert 0.0 == actual['expenses']
    assert 1.0 == actual['balance']
    assert 0.5 == actual['have']
    assert -0.5 == actual['delta']


def test_post_save_account_balace_insert_count_queries(mock_crequest,
                                                       django_assert_max_num_queries):
    AccountBalanceFactory()
    AccountWorthFactory()
    account = AccountFactory()
    income_type = IncomeTypeFactory()

    income = Income(
        date=date(1999, 1, 1),
        price=Decimal(1),
        account=account,
        income_type=income_type
    )
    with django_assert_max_num_queries(15):
        income.save()


def test_post_save_account_balace_update_count_queries(mock_crequest,
                                                       django_assert_max_num_queries):
    AccountBalanceFactory()
    AccountWorthFactory()
    account = AccountFactory()
    income_type = IncomeTypeFactory()

    income = Income(
        date=date(1999, 1, 1),
        price=Decimal(1),
        account=account,
        income_type=income_type
    )
    with django_assert_max_num_queries(17):
        income.save()


def test_post_save_income_type_insert_new(mock_crequest, incomes):
    obj = IncomeType(title='e1')
    obj.save()

    actual = AccountBalance.objects.items()

    assert 2 == actual.count()
