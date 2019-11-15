from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ...bookkeeping.factories import AccountWorthFactory
from ..factories import IncomeFactory, IncomeTypeFactory
from ..models import Income, IncomeType

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Income Type
# ----------------------------------------------------------------------------
def test_income_type_str():
    i = IncomeTypeFactory.build()

    assert str(i) == 'Income Type'


def test_income_type_new_post_save(mock_crequest, incomes):
    obj = IncomeType(title='e1')
    obj.save()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2


# ----------------------------------------------------------------------------
#                                                                       Income
# ----------------------------------------------------------------------------
def test_income_str():
    i = IncomeFactory.build()

    assert str(i) == '1999-01-01: Income Type'


def test_sum_all_months(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]

    actual = list(Income.objects.income_sum(1999))

    assert expect == actual


def test_sum_all_months_ordering(incomes):
    actual = list(Income.objects.income_sum(1999))

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[1]['date'] == date(1999, 2, 1)


def test_sum_one_month(incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)}
    ]

    actual = list(Income.objects.income_sum(1999, 1))

    assert len(expect) == 1
    assert expect == actual


def test_incomes_items():
    IncomeFactory()

    assert len(Income.objects.items()) == 1


def test_incomes_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Income.objects.items().values()


def test_incomes_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Income.objects.year(1999).values()


def test_incomes_income_sum_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Income.objects.income_sum(1999).values()

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


def test_income_month_type_sum():
    IncomeFactory(
        price=4,
        date=date(1999, 1, 2),
        income_type=IncomeTypeFactory(title='I-2')
    )
    IncomeFactory(
        price=3,
        date=date(1999, 1, 1),
        income_type=IncomeTypeFactory(title='I-2')
    )
    IncomeFactory(
        price=1,
        date=date(1974, 1, 1),
        income_type=IncomeTypeFactory(title='I-1')
    )
    IncomeFactory(
        price=2,
        date=date(1999, 1, 2),
        income_type=IncomeTypeFactory(title='I-1')
    )
    IncomeFactory(
        price=1,
        date=date(1999, 1, 1),
        income_type=IncomeTypeFactory(title='I-1')
    )

    expect = [
        {'date': date(1999, 1, 1), 'title': 'I-1', 'sum': Decimal(3)},
        {'date': date(1999, 1, 1), 'title': 'I-2', 'sum': Decimal(7)},
    ]
    actual = Income.objects.month_type_sum(1999)

    assert expect == [*actual]


def test_income_new_post_save(mock_crequest):
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

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 0.0
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0
    assert actual['have'] == 0.5
    assert actual['delta'] == -0.5


def test_income_update_post_save(mock_crequest):
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

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 0.0
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0
    assert actual['have'] == 0.5
    assert actual['delta'] == -0.5


def test_income_new_post_save_count_qs(mock_crequest,
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


def test_income_update_post_save_count_qs(mock_crequest,
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
