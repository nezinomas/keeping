from datetime import date
from decimal import Decimal

import mock
import pytest
from django.core.files import File
from django.db import models
from django.urls import reverse
from freezegun import freeze_time
from override_storage import override_storage

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...expenses.factories import ExpenseFactory
from ...journals.models import Journal
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


def test_expense_type_get_absolute_url():
    obj = ExpenseTypeFactory()

    assert obj.get_absolute_url() == reverse('expenses:type_update', kwargs={'pk': obj.pk})


def test_month_expense_type(expenses):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'Expense Type'},
        {'date': date(1999, 12, 1), 'sum': Decimal(1.25), 'title': 'Expense Type'},
    ]

    actual = [*Expense.objects.sum_by_month_and_type(1999)]

    assert actual == expect


def test_day_expense_type(expenses_january):
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

    actual = [*Expense.objects.sum_by_day_ant_type(1999, 1)]

    assert actual == expect


def test_expense_type_items():
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2')

    actual = ExpenseType.objects.items()

    assert actual.count() == 2


def test_expense_type_items_user(second_user):
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2', journal=second_user.journal)

    actual = ExpenseType.objects.items()

    assert actual.count() == 1


def test_expense_type_related_qs_count(django_assert_max_num_queries):
    ExpenseTypeFactory(title='T1')
    ExpenseTypeFactory(title='T2')
    ExpenseTypeFactory(title='T3')

    with django_assert_max_num_queries(2):
        list(q.title for q in ExpenseType.objects.items())


def test_post_save_expense_type_insert_new(main_user):
    obj = ExpenseType(title='e1', journal=main_user.journal)
    obj.save()

    actual = AccountBalance.objects.items()

    assert actual.count() == 0


@pytest.mark.xfail
def test_expense_type_unique_user():
    ExpenseType.objects.create(title='T1', user=UserFactory())
    ExpenseType.objects.create(title='T1', user=UserFactory())


def test_expense_type_unique_users(main_user, second_user):
    ExpenseType.objects.create(title='T1', journal=main_user.journal)
    ExpenseType.objects.create(title='T1', journal=second_user.journal)


# ----------------------------------------------------------------------------
#                                                                 Expense Name
# ----------------------------------------------------------------------------
def test_expnese_name_str():
    e = ExpenseNameFactory.build()

    assert str(e) == 'Expense Name'

def test_expense_name_get_absolute_url():
    obj = ExpenseNameFactory()

    assert obj.get_absolute_url() == reverse('expenses:name_update', kwargs={'pk': obj.pk})


def test_expense_name_items():
    ExpenseNameFactory(title='N1')
    ExpenseNameFactory(title='N2')

    actual = ExpenseName.objects.items()

    assert actual.count() == 2


def test_expense_name_related_different_users(main_user, second_user):
    t1 = ExpenseTypeFactory(title='T1', journal=main_user.journal) # user bob
    t2 = ExpenseTypeFactory(title='T2', journal=second_user.journal) # user X

    ExpenseNameFactory(title='N1', parent=t1)
    ExpenseNameFactory(title='N2', parent=t2)

    actual = ExpenseName.objects.related()

    # expense names for user bob
    assert len(actual) == 1
    assert actual[0].title == 'N1'


def test_expense_name_related_qs_count(django_assert_max_num_queries):
    ExpenseNameFactory(title='T1')
    ExpenseNameFactory(title='T2')

    with django_assert_max_num_queries(1):
        list(q.parent.title for q in ExpenseName.objects.related())


def test_expense_name_year():
    ExpenseNameFactory(title='N1', valid_for=2000)
    ExpenseNameFactory(title='N2', valid_for=1999)

    actual = ExpenseName.objects.year(2000)

    assert actual.count() == 1
    assert actual[0].title == 'N1'


def test_expense_name_year_02():
    ExpenseNameFactory(title='N1', valid_for=2000)
    ExpenseNameFactory(title='N2')

    actual = ExpenseName.objects.year(2000)

    assert actual.count() == 2
    assert actual[0].title == 'N2'
    assert actual[1].title == 'N1'


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


def test_expense_fields_types():
    assert isinstance(Expense._meta.get_field('date'), models.DateField)
    assert isinstance(Expense._meta.get_field('price'), models.DecimalField)
    assert isinstance(Expense._meta.get_field('quantity'), models.IntegerField)
    assert isinstance(Expense._meta.get_field('expense_type'), models.ForeignKey)
    assert isinstance(Expense._meta.get_field('expense_name'), models.ForeignKey)
    assert isinstance(Expense._meta.get_field('remark'), models.TextField)
    assert isinstance(Expense._meta.get_field('exception'), models.BooleanField)
    assert isinstance(Expense._meta.get_field('account'), models.ForeignKey)
    assert isinstance(Expense._meta.get_field('attachment'), models.FileField)


@override_storage()
@freeze_time("1000-1-1")
def test_expense_attachment_field(get_user):
    file_mock = mock.MagicMock(spec=File, name='FileMock')
    file_mock.name = 'test1.jpg'

    e = ExpenseFactory(attachment=file_mock)
    pk = str(get_user.journal.pk)

    assert str(e.attachment) == f'{pk}/expense-type/1000.01_test1.jpg'


def test_expense_related(second_user):
    t1 = ExpenseTypeFactory(title='T1')  # user bob, current user
    t2 = ExpenseTypeFactory(title='T2', journal=second_user.journal)  # user X

    ExpenseFactory(expense_type=t1)
    ExpenseFactory(expense_type=t2)

    # must by selected bob expenses
    actual = Expense.objects.related()

    assert len(actual) == 1
    assert str(actual[0].expense_type) == 'T1'


def test_expense_year():
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = Expense.objects.year(2000)

    assert actual.count() == 1


def test_expense_year_query_count(django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        list(q.expense_type for q in Expense.objects.year(2000))


def test_expense_items():
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    actual = Expense.objects.items()

    assert actual.count() == 2


def test_expense_items_query_count(django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1))
    ExpenseFactory(date=date(2000, 1, 1))

    with django_assert_max_num_queries(1):
        list(q.expense_type.title for q in Expense.objects.items())


def test_month_name_sum():
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

    actual = Expense.objects.sum_by_month_and_name(1999)

    assert [*actual] == expect


@freeze_time('1999-06-01')
def test_expense_avg_last_months():
    ExpenseFactory(date=date(1998, 11, 30), price=3)
    ExpenseFactory(date=date(1998, 12, 31), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=7)

    actual = Expense.objects.last_months(6)

    assert actual.count() == 1
    assert actual[0]['sum'] == 11.0
    assert actual[0]['title'] == 'Expense Type'


@freeze_time('1999-06-01')
def test_expense_avg_last_months_qs_count(django_assert_max_num_queries):
    ExpenseFactory(date=date(1999, 1, 1), price=2)

    with django_assert_max_num_queries(1):
        print(Expense.objects.last_months())


def test_expense_years_sum():
    ExpenseFactory(date=date(1998, 1, 1), price=4.0)
    ExpenseFactory(date=date(1998, 1, 1), price=4.0)
    ExpenseFactory(date=date(1999, 1, 1), price=5.0)
    ExpenseFactory(date=date(1999, 1, 1), price=5.0)

    actual = Expense.objects.sum_by_year()

    assert actual[0]['year'] == 1998
    assert actual[0]['sum'] == 8.0

    assert actual[1]['year'] == 1999
    assert actual[1]['sum'] == 10.0


def test_expense_sum_by_month():
    ExpenseFactory(date=date(1999, 2, 3), price=2.0)
    ExpenseFactory(date=date(1999, 2, 12), price=4.0)
    ExpenseFactory(date=date(1999, 1, 31), price=2.0)
    ExpenseFactory(date=date(1999, 1, 13), price=1.0)

    actual = Expense.objects.sum_by_month(1999)

    assert list(actual) == [
        {'sum': Decimal('3'), 'date': date(1999, 1, 1)},
        {'sum': Decimal('6'), 'date': date(1999, 2, 1)}
    ]


def test_expense_updates_journal_first_record():
    assert Journal.objects.first().first_record == date(1999, 1, 1)

    ExpenseFactory(date=date(1974, 2, 2))

    assert Journal.objects.first().first_record == date(1974, 2, 2)


# ----------------------------------------------------------------------------
#                                                         Expense post signals
# ----------------------------------------------------------------------------
def test_expense_new_post_save():
    ExpenseFactory(price=1)

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == 'Account1'
    assert actual.expenses == 1.0
    assert actual.balance == -1.0


def test_expense_update_post_save():
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory()

    obj = Expense.objects.create(
        date=date(1999, 1, 1),
        price=1.12,
        quantity=1,
        account=a,
        expense_type=t,
        expense_name=n
    )

    # update
    obj_update = Expense.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == 'Account1'
    assert actual.expenses == 1.0
    assert actual.balance == -1.0


def test_expense_post_save_update_with_nothing_changed():
    obj = ExpenseFactory(price=5)

    # update price
    obj_update = Expense.objects.get(pk=obj.pk)
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.account.title == 'Account1'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_expense_post_save_change_account():
    account_old = AccountFactory()
    account_new = AccountFactory(title='XXX')

    obj = ExpenseFactory(price=5, account=account_old)

    actual = AccountBalance.objects.get(account_id=account_old.pk)
    assert actual.account.title == 'Account1'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0

    # update account
    obj_new = Expense.objects.get(account_id=obj.pk)
    obj_new.account = account_new
    obj_new.save()

    doest_not_exists = False
    try:
        AccountBalance.objects.get(account_id=account_old.pk)
    except AccountBalance.DoesNotExist:
        doest_not_exists = True

    assert doest_not_exists

    actual = AccountBalance.objects.get(account_id=account_new.pk)
    assert actual.account.title == 'XXX'
    assert actual.incomes == 0.0
    assert actual.expenses == 5.0
    assert actual.balance == -5.0


def test_expense_post_delete():
    ExpenseFactory()

    Expense.objects.first().delete()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 0
    assert Expense.objects.all().count() == 0


def test_expense_post_delete_with_update():
    ExpenseFactory(date=date(1974, 1, 1), price=5)
    obj = ExpenseFactory(date=date(1999, 1, 1), price=1)

    # check before delete
    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == Decimal('-5')
    assert actual.incomes == Decimal('0')
    assert actual.expenses == Decimal('1')
    assert actual.balance == Decimal('-6')
    assert actual.delta == Decimal('6')

    # delete Expense object
    Expense.objects.get(pk=obj.pk).delete()

    fail = False
    try:
        AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    except AccountBalance.DoesNotExist:
        fail = True
    assert fail


def test_expense_post_save_first_year_record():
    obj1 = ExpenseFactory(date=date(1974, 1, 1), price=5)

    # truncate account balance table
    AccountBalance.objects.all().delete()

    obj2 = ExpenseFactory(date=date(1999, 1, 1), price=1)


    actual = AccountBalance.objects.get(account_id=obj2.account.pk, year=1999)
    assert actual.past == Decimal('-5')
    assert actual.incomes == Decimal('0')
    assert actual.expenses == Decimal('1')
    assert actual.balance == Decimal('-6')
    assert actual.delta == Decimal('6')

    actual = AccountBalance.objects.get(account_id=obj1.account.pk, year=1974)
    assert actual.past == Decimal('0')
    assert actual.incomes == Decimal('0')
    assert actual.expenses == Decimal('5')
    assert actual.balance == Decimal('-5')
    assert actual.delta == Decimal('5')


def test_expense_post_save_update_balance_row():
    ExpenseFactory(date=date(1974, 1, 1), price=5)
    obj = ExpenseFactory(date=date(1999, 1, 1), price=1)

    actual = AccountBalance.objects.get(account_id=obj.account.pk, year=1999)
    assert actual.past == Decimal('-5')
    assert actual.incomes == Decimal('0')
    assert actual.expenses == Decimal('1')
    assert actual.balance == Decimal('-6')
    assert actual.delta == Decimal('6')


def test_expense_post_delete_empty_account_balance_table():
    # past data
    obj_stay = ExpenseFactory(date=date(1974, 1, 1), price=5)
    obj_del = ExpenseFactory(date=date(1999, 1, 1), price=1)

    AccountBalance.objects.all().delete()

    # delete Expense object
    Expense.objects.get(pk=obj_del.pk).delete()

    actual = AccountBalance.objects.all()

    assert actual.count() == 1
    assert actual[0].account_id == obj_stay.account.pk
    assert actual[0].year == 1974
    assert actual[0].past == Decimal('0')
    assert actual[0].incomes == Decimal('0')
    assert actual[0].expenses == Decimal('5')
    assert actual[0].balance == Decimal('-5')
    assert actual[0].delta == Decimal('5')


def test_expense_sum_by_year_type():
    ExpenseFactory(date=date(1111, 1, 1), price=1)
    ExpenseFactory(date=date(1999, 1, 1), price=2)
    ExpenseFactory(date=date(1111, 1, 1), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=10)

    actual = Expense.objects.sum_by_year_type()

    assert actual[0]['year'] == 1111
    assert actual[0]['title'] == 'Expense Type'
    assert actual[0]['sum'] == Decimal('5')
    assert actual[1]['year'] == 1999
    assert actual[1]['title'] == 'Expense Type'
    assert actual[1]['sum'] == Decimal('12')


def test_expense_sum_by_year_type_filtering():
    t1 = ExpenseTypeFactory(title='X')
    t2 = ExpenseTypeFactory(title='Y')

    ExpenseFactory(expense_type=t1, date=date(1111, 1, 1), price=1)
    ExpenseFactory(expense_type=t1, date=date(1999, 1, 1), price=2)
    ExpenseFactory(expense_type=t1, date=date(1111, 1, 1), price=4)
    ExpenseFactory(expense_type=t1, date=date(1999, 1, 1), price=10)

    ExpenseFactory(expense_type=t2, date=date(1111, 1, 1), price=1.1)
    ExpenseFactory(expense_type=t2, date=date(1999, 1, 1), price=2.1)
    ExpenseFactory(expense_type=t2, date=date(1111, 1, 1), price=4.1)
    ExpenseFactory(expense_type=t2, date=date(1999, 1, 1), price=10.1)

    actual = Expense.objects.sum_by_year_type(expense_type=[t1.pk])

    assert actual[0]['year'] == 1111
    assert actual[0]['title'] == 'X'
    assert actual[0]['sum'] == Decimal('5')
    assert actual[1]['year'] == 1999
    assert actual[1]['title'] == 'X'
    assert actual[1]['sum'] == Decimal('12')


def test_expense_sum_by_year_name():
    ExpenseFactory(date=date(1111, 1, 1), price=1)
    ExpenseFactory(date=date(1999, 1, 1), price=2)
    ExpenseFactory(date=date(1111, 1, 1), price=4)
    ExpenseFactory(date=date(1999, 1, 1), price=10)

    actual = Expense.objects.sum_by_year_name()

    assert actual[0]['year'] == 1111
    assert actual[0]['title'] == 'Expense Type / Expense Name'
    assert actual[0]['sum'] == Decimal('5')

    assert actual[1]['year'] == 1999
    assert actual[1]['title'] == 'Expense Type / Expense Name'
    assert actual[1]['sum'] == Decimal('12')


def test_expense_sum_by_year_name_filtering():
    t1 = ExpenseNameFactory(title='X')
    t2 = ExpenseNameFactory(title='Y')

    ExpenseFactory(expense_name=t1, date=date(1111, 1, 1), price=1)
    ExpenseFactory(expense_name=t1, date=date(1999, 1, 1), price=2)
    ExpenseFactory(expense_name=t1, date=date(1111, 1, 1), price=4)
    ExpenseFactory(expense_name=t1, date=date(1999, 1, 1), price=10)

    ExpenseFactory(expense_name=t2, date=date(1111, 1, 1), price=1.1)
    ExpenseFactory(expense_name=t2, date=date(1999, 1, 1), price=2.1)
    ExpenseFactory(expense_name=t2, date=date(1111, 1, 1), price=4.1)
    ExpenseFactory(expense_name=t2, date=date(1999, 1, 1), price=10.1)

    actual = Expense.objects.sum_by_year_name(expense_name=[t1.pk])

    assert actual[0]['year'] == 1111
    assert actual[0]['title'] == 'Expense Type / X'
    assert actual[0]['sum'] == Decimal('5')

    assert actual[1]['year'] == 1999
    assert actual[1]['title'] == 'Expense Type / X'
    assert actual[1]['sum'] == Decimal('12')


def test_expenses(expenses):
    actual = Expense.objects.expenses()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['expenses'] == 2.5

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['expenses'] == 2.25

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['expenses'] == 0.5

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['expenses'] == 1.25
