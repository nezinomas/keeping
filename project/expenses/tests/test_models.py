from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...expenses.factories import ExpenseFactory
from ..factories import ExpenseFactory, ExpenseNameFactory, ExpenseTypeFactory
from ..models import Expense, ExpenseName, ExpenseType

pytestmark = pytest.mark.django_db


@pytest.fixture()
def expenses_more():
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=0.30,
        account=AccountFactory(title='Account1'),
        exception=True
    )


def test_month_expense_type(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 12, 1), 'sum': Decimal(1.25), 'title': 'Expense Type'},
    ]

    actual = [*Expense.objects.month_expense_type(1999)]

    assert expect == actual


def test_month_expense_type_one_month(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
    ]

    actual = [*Expense.objects.month_expense_type(1999, 1)]

    assert expect == actual


def test_day_expense_type(expenses_january):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 1, 11), 'sum': Decimal(0.5), 'title': 'Expense Type'},
    ]

    actual = [*Expense.objects.day_expense_type(1999, 1)]

    assert expect == actual


def test_month_exception_sum(expenses_january, expenses_more):
    actual = [*Expense.objects.month_exceptions(1999, 1)]

    assert date(1999, 1, 1) == actual[0]['date']
    assert 'Expense Type' == actual[0]['title']
    assert round(Decimal(0.55), 2) == round(actual[0]['sum'], 2)


def test_expense_str():
    e = ExpenseFactory.build()

    assert '1999-01-01/Expense Type/Expense Name' == str(e)


def test_expense_type_str():
    e = ExpenseTypeFactory.build()

    assert 'Expense Type' == str(e)


def test_expnese_name_str():
    e = ExpenseNameFactory.build()

    assert 'Expense Name' == str(e)


def test_expense_year():
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = Expense.objects.year(2000)

    assert 1 == actual.count()


def test_expense_year_query_count(django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        list(Expense.objects.year(2000).values())


def test_expense_items():
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = Expense.objects.items()

    assert 2 == actual.count()


def test_expense_items_query_count(django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        list(Expense.objects.items().values('expense_type__title'))


def test_expense_type_items():
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2')

    actual = ExpenseType.objects.items()

    assert 2 == actual.count()


def test_expense_type_items_query_count(django_assert_max_num_queries):
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2')

    with django_assert_max_num_queries(1):
        list(ExpenseType.objects.items().values())


def test_expense_name_items():
    ExpenseNameFactory(title='N1')
    ExpenseNameFactory(title='N2')

    actual = ExpenseName.objects.items()

    assert 2 == actual.count()


def test_expense_name_year():
    ExpenseNameFactory(title='N1', valid_for=2000)
    ExpenseNameFactory(title='N2', valid_for=1999)

    actual = ExpenseName.objects.year(2000)

    assert 1 == actual.count()
    assert 'N1' == actual[0].title


def test_expense_name_year_02():
    ExpenseNameFactory(title='N1', valid_for=2000)
    ExpenseNameFactory(title='N2')

    actual = ExpenseName.objects.year(2000)

    assert 2 == actual.count()
    assert 'N2' == actual[0].title
    assert 'N1' == actual[1].title


def test_expense_name_parent():
    p1 = ExpenseTypeFactory(title='P1')
    p2 = ExpenseTypeFactory(title='P2')

    ExpenseNameFactory(title='N1', parent=p1)
    ExpenseNameFactory(title='N2', parent=p1)
    ExpenseNameFactory(title='N3', parent=p2)

    actual = ExpenseName.objects.parent(p1.pk)

    assert 2 == actual.count()


@pytest.mark.django_db
@pytest.mark.xfail(raises=Exception)
def test_expense_name_no_dublicates():
    p1 = ExpenseTypeFactory(title='P1')

    ExpenseName(title='N1', parent=p1).save()
    ExpenseName(title='N1', parent=p1).save()


def test_summary(expenses):
    expect = [{
        'title': 'Account1',
        'e_past': 2.5,
        'e_now': 0.5,

    }, {
        'title': 'Account2',
        'e_past': 2.25,
        'e_now': 1.25,
    }]

    actual = [*Expense.objects.summary(1999).order_by('account__title')]

    assert expect == actual


# ----------------------------------------------------------------------------
#                                                             post_save signal
# ----------------------------------------------------------------------------
def test_post_save_expense_type_insert_new(mock_crequest, expenses):
    obj = ExpenseType(title='e1')
    obj.save()

    actual = AccountBalance.objects.items()

    assert 2 == actual.count()
