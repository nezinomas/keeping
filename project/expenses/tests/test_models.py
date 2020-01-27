from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...expenses.factories import ExpenseFactory
from ...users.factories import UserFactory
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


# ----------------------------------------------------------------------------
#                                                                 Expense Type
# ----------------------------------------------------------------------------
def test_expense_type_str():
    e = ExpenseTypeFactory.build()

    assert str(e) == 'Expense Type'


def test_month_expense_type(get_user, expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 12, 1), 'sum': Decimal(1.25), 'title': 'Expense Type'},
    ]

    actual = [*Expense.objects.month_expense_type(1999)]

    assert actual == expect


def test_day_expense_type(get_user, expenses_january):
    expect = [
        {
            'date': date(1999, 1, 1),
            'sum': Decimal(0.5),
            'title': 'Expense Type',
            'exception_sum': Decimal(0.25),
        }, {
            'date': date(1999, 1, 11),
            'sum': Decimal(0.5),
            'title': 'Expense Type',
            'exception_sum': Decimal(0),
        },
    ]

    actual = [*Expense.objects.day_expense_type(1999, 1)]

    assert actual == expect


def test_expense_type_items(get_user):
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2')

    actual = ExpenseType.objects.items()

    assert actual.count() == 2


def test_expense_type_items_user(get_user):
    ExpenseTypeFactory(title='T1', user=UserFactory())
    ExpenseTypeFactory(title='T2', user=UserFactory(username='u2'))

    actual = ExpenseType.objects.items()

    assert actual.count() == 1


def test_expense_type_related_qs_count(django_assert_max_num_queries, get_user):
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2')
    ExpenseTypeFactory(title='T3')

    with django_assert_max_num_queries(2):
        list(q.title for q in ExpenseType.objects.items())


def test_post_save_expense_type_insert_new(get_user, expenses):
    obj = ExpenseType(title='e1', user=UserFactory())
    obj.save()

    actual = AccountBalance.objects.items()

    assert actual.count() == 2


@pytest.mark.xfail
def test_expense_type_unique_user(get_user):
    ExpenseType.objects.create(title='T1', user=UserFactory())
    ExpenseType.objects.create(title='T1', user=UserFactory())


def test_expense_type_unique_users(get_user):
    ExpenseType.objects.create(title='T1', user=UserFactory(username='x'))
    ExpenseType.objects.create(title='T1', user=UserFactory(username='y'))


# ----------------------------------------------------------------------------
#                                                                 Expense Name
# ----------------------------------------------------------------------------
def test_expnese_name_str():
    e = ExpenseNameFactory.build()

    assert str(e) == 'Expense Name'


def test_expense_name_items(get_user):
    ExpenseNameFactory(title='N1')
    ExpenseNameFactory(title='N2')

    actual = ExpenseName.objects.items()

    assert actual.count() == 2


def test_expense_name_related_different_users(get_user):
    u = UserFactory(username='tom')

    t1 = ExpenseTypeFactory(title='T1') # user bob
    t2 = ExpenseTypeFactory(title='T2', user=u) # user tom

    ExpenseNameFactory(title='N1', parent=t1)
    ExpenseNameFactory(title='N2', parent=t2)

    actual = ExpenseName.objects.related()

    # expense names for user bob
    assert len(actual) == 1
    assert actual[0].title == 'N1'


def test_expense_name_related_qs_count(get_user, django_assert_max_num_queries):
    ExpenseNameFactory(title='T1')
    ExpenseNameFactory(title='T2')

    with django_assert_max_num_queries(1):
        list(q.parent.title for q in ExpenseName.objects.related())


def test_expense_name_year(get_user):
    ExpenseNameFactory(title='N1', valid_for=2000)
    ExpenseNameFactory(title='N2', valid_for=1999)

    actual = ExpenseName.objects.year(2000)

    assert actual.count() == 1
    assert actual[0].title == 'N1'


def test_expense_name_year_02(get_user):
    ExpenseNameFactory(title='N1', valid_for=2000)
    ExpenseNameFactory(title='N2')

    actual = ExpenseName.objects.year(2000)

    assert actual.count() == 2
    assert actual[0].title == 'N2'
    assert actual[1].title == 'N1'


def test_expense_name_parent(get_user):
    p1 = ExpenseTypeFactory(title='P1')
    p2 = ExpenseTypeFactory(title='P2')

    ExpenseNameFactory(title='N1', parent=p1)
    ExpenseNameFactory(title='N2', parent=p1)
    ExpenseNameFactory(title='N3', parent=p2)

    actual = ExpenseName.objects.parent(p1.pk)

    assert actual.count() == 2


@pytest.mark.django_db
@pytest.mark.xfail(raises=Exception)
def test_expense_name_no_dublicates():
    p1 = ExpenseTypeFactory(title='P1')

    ExpenseName(title='N1', parent=p1).save()
    ExpenseName(title='N1', parent=p1).save()


# ----------------------------------------------------------------------------
#                                                                      Expense
# ----------------------------------------------------------------------------
def test_expense_str():
    e = ExpenseFactory.build()

    assert str(e) == '1999-01-01/Expense Type/Expense Name'


def test_expense_related(get_user):
    u = UserFactory(username='tom')

    t1 = ExpenseTypeFactory(title='T1')  # user bob, current user
    t2 = ExpenseTypeFactory(title='T2', user=u)  # user tom

    ExpenseFactory(expense_type=t1)
    ExpenseFactory(expense_type=t2)

    # must by selected bob expenses
    actual = Expense.objects.related()

    assert len(actual) == 1
    assert str(actual[0].expense_type) == 'T1'


def test_expense_year(get_user):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = Expense.objects.year(2000)

    assert actual.count() == 1


def test_expense_year_query_count(get_user, django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        list(q.expense_type for q in Expense.objects.year(2000))


def test_expense_items(get_user):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = Expense.objects.items()

    assert actual.count() == 2


def test_expense_items_query_count(get_user, django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        list(q.expense_type.title for q in Expense.objects.items())


def test_month_name_sum(get_user):
    ExpenseFactory(
        date=date(1974, 1, 1),
        price=1,
        expense_type=ExpenseTypeFactory(title='T1'),
        expense_name=ExpenseNameFactory(title='N1')
    )
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=2,
        expense_type=ExpenseTypeFactory(title='T1'),
        expense_name=ExpenseNameFactory(title='N1')
    )
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=3,
        expense_type=ExpenseTypeFactory(title='T2'),
        expense_name=ExpenseNameFactory(title='N1')
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        price=4,
        expense_type=ExpenseTypeFactory(title='T1'),
        expense_name=ExpenseNameFactory(title='N1')
    )
    ExpenseFactory(
        date=date(1999, 2, 1),
        price=5,
        expense_type=ExpenseTypeFactory(title='T1'),
        expense_name=ExpenseNameFactory(title='N1')
    )

    expect = [
        {'date': date(1999, 1, 1), 'title': 'N1', 'type_title': 'T1', 'sum': Decimal(2)},
        {'date': date(1999, 1, 1), 'title': 'N1', 'type_title': 'T2', 'sum': Decimal(3)},
        {'date': date(1999, 2, 1), 'title': 'N1', 'type_title': 'T1', 'sum': Decimal(9)},
    ]

    actual = Expense.objects.month_name_sum(1999)

    assert [*actual] == expect


def test_summary(get_user, expenses):
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

    assert actual == expect


@freeze_time('1999-06-01')
def test_expense_avg_last_six_months_full(get_user):
    ExpenseFactory(date=date(1998, 1, 1), price=10)
    ExpenseFactory(date=date(1999, 1, 1), price=1)
    ExpenseFactory(date=date(1999, 1, 1), price=2)
    ExpenseFactory(date=date(1999, 6, 1), price=4)

    actual = Expense.objects.last_six_months()

    assert round(actual, 2) == 1.17


@freeze_time('1999-06-01')
def test_expense_avg_last_six_months_cut(get_user):
    ExpenseFactory(date=date(1999, 1, 1), price=1, expense_type=ExpenseTypeFactory(title='x'))
    ExpenseFactory(date=date(1999, 1, 1), price=2, expense_type=ExpenseTypeFactory(title='x'))
    ExpenseFactory(date=date(1999, 6, 1), price=4, expense_type=ExpenseTypeFactory(title='y'))

    actual = Expense.objects.last_six_months(['x'])

    assert round(actual, 2) == 0.5
