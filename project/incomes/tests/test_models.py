from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ...users.factories import UserFactory
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


def test_income_type_items_user(get_user):
    IncomeTypeFactory(title='T1', user=UserFactory())
    IncomeTypeFactory(title='T2', user=UserFactory(username='u2'))

    actual = IncomeType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


def test_income_type_new_post_save(get_user, incomes):
    # befor post_save AccountBalance empty
    actual = AccountBalance.objects.items()
    assert len(actual) == 0

    obj = IncomeType(title='T1', user=UserFactory())
    obj.save()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2


@pytest.mark.xfail
def test_income_type_unique_for_user(get_user):
    IncomeType.objects.create(title='T', user=UserFactory())
    IncomeType.objects.create(title='T', user=UserFactory())


def test_income_type_unique_for_users(get_user):
    IncomeType.objects.create(title='T', user=UserFactory(username='x'))
    IncomeType.objects.create(title='T', user=UserFactory(username='y'))


# ----------------------------------------------------------------------------
#                                                                       Income
# ----------------------------------------------------------------------------
def test_income_str():
    i = IncomeFactory.build()

    assert str(i) == '1999-01-01: Income Type'


def test_income_related(get_user):
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')
    t1 = IncomeTypeFactory(title='T1', user=u1)
    t2 = IncomeTypeFactory(title='T2', user=u2)

    IncomeFactory(income_type=t1)
    IncomeFactory(income_type=t2)

    actual = Income.objects.related()

    assert len(actual) == 1
    assert str(actual[0].income_type) == 'T1'


def test_sum_all_months(get_user, incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)},
        {'date': date(1999, 2, 1), 'sum': Decimal(1.25)},
    ]

    actual = list(Income.objects.income_sum(1999))

    assert expect == actual


def test_sum_all_months_ordering(get_user, incomes):
    actual = list(Income.objects.income_sum(1999))

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[1]['date'] == date(1999, 2, 1)


def test_sum_one_month(get_user, incomes):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5.5)}
    ]

    actual = list(Income.objects.income_sum(1999, 1))

    assert len(expect) == 1
    assert expect == actual


def test_incomes_items(get_user):
    IncomeFactory()

    assert len(Income.objects.items()) == 1


def test_incomes_items_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Income.objects.items().values()


def test_incomes_year_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Income.objects.year(1999).values()


def test_incomes_income_sum_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Income.objects.income_sum(1999).values()

def test_summary(get_user, incomes):
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


def test_income_month_type_sum(get_user):
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


def test_income_new_post_save(get_user):
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

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 0.0
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0
    assert actual['have'] == 0.5
    assert actual['delta'] == -0.5


def test_income_update_post_save(get_user):
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

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 0.0
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0
    assert actual['have'] == 0.5
    assert actual['delta'] == -0.5


def test_income_new_post_save_count_qs(get_user,
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


def test_income_update_post_save_count_qs(get_user,
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


def test_income_years_sum(get_user):
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1998, 1, 1), price=4.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)
    IncomeFactory(date=date(1999, 1, 1), price=5.0)

    actual = Income.objects.year_income()

    assert actual[0]['year'] == 1998
    assert actual[0]['sum'] == 8.0

    assert actual[1]['year'] == 1999
    assert actual[1]['sum'] == 10.0
