from datetime import date as dt
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...incomes.factories import IncomeFactory
from ..factories import (BorrowFactory, BorrowReturnFactory, LendFactory,
                         LendReturnFactory)
from ..models import Debt, DebtReturn

pytestmark = pytest.mark.django_db


def test_lend_return_str():
    v = LendReturnFactory.build()

    assert str(v) == 'Grąžino 5.0'


def test_borrow_return_str():
    v = BorrowReturnFactory.build()

    assert str(v) == 'Grąžinau 5.0'


def test_debt_return_fields():
    assert DebtReturn._meta.get_field('date')
    assert DebtReturn._meta.get_field('price')
    assert DebtReturn._meta.get_field('account')
    assert DebtReturn._meta.get_field('debt')
    assert DebtReturn._meta.get_field('remark')


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_related(mck, main_user, second_user):
    b1 = LendFactory(name='B1', price=1, journal=main_user.journal)
    b2 = LendFactory(name='B2', price=2, journal=second_user.journal)

    LendReturnFactory(debt=b1, price=1.1)
    LendReturnFactory(debt=b2, price=2.1)

    actual = DebtReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžino 1.1'


@patch('project.core.lib.utils.get_request_kwargs', return_value='borrow')
def test_borrow_return_related(mck, main_user, second_user):
    b1 = BorrowFactory(name='B1', price=1, journal=main_user.journal)
    b2 = BorrowFactory(name='B2', price=2, journal=second_user.journal)

    BorrowReturnFactory(debt=b1, price=1.1)
    BorrowReturnFactory(debt=b2, price=2.1)

    actual = DebtReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžinau 1.1'


def test_lend_return_related_queries(django_assert_num_queries):
    LendReturnFactory()
    LendReturnFactory()

    with django_assert_num_queries(1):
        list(x.account.title for x in list(DebtReturn.objects.related()))


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_items(mck):
    LendReturnFactory()
    LendReturnFactory()

    actual = DebtReturn.objects.items()

    assert actual.count() == 2


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_year(mck):
    LendReturnFactory()
    LendReturnFactory(date=dt(1974, 1, 2))

    actual = DebtReturn.objects.year(1999)

    assert actual.count() == 1


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_new_record_updates_debt_tbl(mck):
    LendReturnFactory()

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_update(mck):
    obj = LendReturnFactory()

    actual = Debt.objects.items()
    assert actual[0].returned == Decimal('30')

    obj.price = Decimal('20')
    obj.save()

    assert DebtReturn.objects.items().count() == 1

    actual = Debt.objects.items()
    assert actual[0].returned == Decimal('45')


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_new_record_updates_debt_tbl_empty_returned_field(mck):
    LendReturnFactory(debt=LendFactory(returned=None))

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('5')


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
@patch('project.debts.models.Debt.objects.filter')
def test_lend_return_new_record_updates_debt_tbl_error_on_save_parent(mck, m):
    mck.side_effect = TypeError

    try:
        LendReturnFactory()
    except TypeError:
        pass

    actual = Debt.objects.items()
    assert actual[0].returned == Decimal('25')

    assert DebtReturn.objects.count() == 0


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_delete_record_updates_debt_tbl(mck):
    obj = LendReturnFactory()

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')

    obj.delete()

    actual = Debt.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('25')


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_delete_record_updates_debt_tbl_error_on_save(mck):
    obj = LendReturnFactory()

    actual = Debt.objects.items()

    assert actual[0].returned == Decimal('30')

    with patch('project.debts.models.super') as mck:
        mck.side_effect = TypeError

        try:
            obj.delete()
        except:
            pass

    actual = Debt.objects.items()

    assert actual[0].returned == Decimal('30')


def test_lend_return_post_save_new():
    LendReturnFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]
    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 5.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -95.0


def test_borrow_return_post_save_new():
    BorrowReturnFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]
    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 5.0
    assert actual['balance'] == 95.0


def test_lend_return_post_save_update():
    obj = LendReturnFactory()

    actual = AccountBalance.objects.first()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 5.0
    assert actual.expenses == 100.0
    assert actual.balance == -95.0

    # update object
    obj_update = DebtReturn.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.first()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 1.0
    assert actual.expenses == 100.0
    assert actual.balance == -99.0


def test_borrow_return_post_save_update():
    obj = BorrowReturnFactory()

    actual = AccountBalance.objects.first()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 5.0
    assert actual.balance == 95.0

    # update object
    obj_update = DebtReturn.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.first()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 1.0
    assert actual.balance == 99.0


def test_lend_return_post_save_first_record():
    l = LendFactory(price=5)

    IncomeFactory(date=dt(1998, 1, 1), price=1)

    # truncate AccountBalance table
    AccountBalance.objects.all().delete()

    LendReturnFactory(date=dt(1999, 1, 1), debt=l, price=2)

    actual = AccountBalance.objects.items()

    assert actual[0].year == 1998
    assert actual[0].past == 0.0
    assert actual[0].incomes == 1.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 1.0
    assert actual[0].delta == -1.0

    assert actual[1].year == 1999
    assert actual[1].past == 1.0
    assert actual[1].incomes == 2.0
    assert actual[1].expenses == 5.0
    assert actual[1].balance == -2.0
    assert actual[1].delta == 2.0


def test_borrow_return_post_save_first_record():
    l = BorrowFactory(price=5)

    IncomeFactory(date=dt(1998, 1, 1), price=1)

    # truncate AccountBalance table
    AccountBalance.objects.all().delete()

    BorrowReturnFactory(date=dt(1999, 1, 1), debt=l, price=2)

    actual = AccountBalance.objects.items()

    assert actual[0].year == 1998
    assert actual[0].past == 0.0
    assert actual[0].incomes == 1.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 1.0
    assert actual[0].delta == -1.0

    assert actual[1].year == 1999
    assert actual[1].past == 1.0
    assert actual[1].incomes == 5.0
    assert actual[1].expenses == 2.0
    assert actual[1].balance == 4.0
    assert actual[1].delta == -4.0


def test_lend_return_post_delete():
    obj = LendReturnFactory()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 5.0
    assert actual.expenses == 100.0
    assert actual.balance == -95.0

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 0.0
    assert actual.expenses == 100.0
    assert actual.balance == -100.0


def test_borrow_return_post_delete():
    obj = BorrowReturnFactory()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 5.0
    assert actual.balance == 95.0

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 0.0
    assert actual.balance == 100.0


def test_lend_return_post_delete_with_updt():
    b = LendFactory()
    LendReturnFactory(debt=b, price=1)

    obj = LendReturnFactory(debt=b, price=2)

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 3.0
    assert actual.expenses == 100.0
    assert actual.balance == -97.0

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 1.0
    assert actual.expenses == 100.0
    assert actual.balance == -99.0


def test_borrow_return_post_delete_with_updt():
    b = BorrowFactory()
    BorrowReturnFactory(debt=b, price=1)

    obj = BorrowReturnFactory(debt=b, price=2)

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 3.0
    assert actual.balance == 97.0

    DebtReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 100.0
    assert actual.expenses == 1.0
    assert actual.balance == 99.0


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_sum_all_months(mck):
    LendReturnFactory(date=dt(1999, 1, 1), price=1)
    LendReturnFactory(date=dt(1999, 1, 2), price=2)
    LendReturnFactory(date=dt(1999, 2, 1), price=4)
    LendReturnFactory(date=dt(1999, 2, 2), price=1)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')},
        {'date': dt(1999, 2, 1), 'sum': Decimal('5')},
    ]

    actual = list(DebtReturn.objects.sum_by_month(1999))

    assert expect == actual


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_sum_all_months_ordering(mck):
    LendReturnFactory(date=dt(1999, 1, 1), price=1)
    LendReturnFactory(date=dt(1999, 1, 2), price=2)
    LendReturnFactory(date=dt(1999, 2, 1), price=4)
    LendReturnFactory(date=dt(1999, 2, 2), price=1)

    actual = list(DebtReturn.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


@patch('project.core.lib.utils.get_request_kwargs', return_value='lend')
def test_lend_return_sum_one_month(mck):
    LendReturnFactory(date=dt(1999, 1, 1), price=1)
    LendReturnFactory(date=dt(1999, 1, 2), price=2)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')}
    ]

    actual = list(DebtReturn.objects.sum_by_month(1999, 1))

    assert len(expect) == 1
    assert expect == actual


def test_lend_return_autoclose():
    LendReturnFactory(price=75)

    actual = Debt.objects.first()

    assert actual.returned == Decimal('100')
    assert actual.closed


def test_debt_return_incomes():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    LendReturnFactory(date=dt(1970, 1, 1), account=a1, price=1)
    LendReturnFactory(date=dt(1970, 1, 1), account=a1, price=2)
    LendReturnFactory(date=dt(1970, 1, 1), account=a2, price=3)
    LendReturnFactory(date=dt(1970, 1, 1), account=a2, price=4)

    LendReturnFactory(date=dt(1999, 1, 1), account=a1, price=10)
    LendReturnFactory(date=dt(1999, 1, 1), account=a1, price=20)
    LendReturnFactory(date=dt(1999, 1, 1), account=a2, price=30)
    LendReturnFactory(date=dt(1999, 1, 1), account=a2, price=40)

    BorrowReturnFactory(date=dt(1999, 1, 1), account=a2, price=180)

    actual = DebtReturn.objects.incomes()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['incomes'] == 3

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['incomes'] == 7

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['incomes'] == 30

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['incomes'] == 70


def test_debt_return_expenses():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    BorrowReturnFactory(date=dt(1970, 1, 1), account=a1, price=1)
    BorrowReturnFactory(date=dt(1970, 1, 1), account=a1, price=2)
    BorrowReturnFactory(date=dt(1970, 1, 1), account=a2, price=3)
    BorrowReturnFactory(date=dt(1970, 1, 1), account=a2, price=4)

    BorrowReturnFactory(date=dt(1999, 1, 1), account=a1, price=10)
    BorrowReturnFactory(date=dt(1999, 1, 1), account=a1, price=20)
    BorrowReturnFactory(date=dt(1999, 1, 1), account=a2, price=30)
    BorrowReturnFactory(date=dt(1999, 1, 1), account=a2, price=40)

    LendReturnFactory(date=dt(1999, 1, 1), account=a2, price=180)

    actual = DebtReturn.objects.expenses()

    assert actual[0]['year'] == 1970
    assert actual[0]['id'] == 1
    assert actual[0]['expenses'] == 3

    assert actual[1]['year'] == 1970
    assert actual[1]['id'] == 2
    assert actual[1]['expenses'] == 7

    assert actual[2]['year'] == 1999
    assert actual[2]['id'] == 1
    assert actual[2]['expenses'] == 30

    assert actual[3]['year'] == 1999
    assert actual[3]['id'] == 2
    assert actual[3]['expenses'] == 70
