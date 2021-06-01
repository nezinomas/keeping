from datetime import date
from datetime import date as dt
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...users.factories import UserFactory
from ..factories import (BorrowFactory, BorrowReturnFactory, LentFactory,
                         LentReturnFactory)
from ..models import Borrow, BorrowReturn, Lent, LentReturn

pytestmark = pytest.mark.django_db


#----------------------------------------------------------------------------------------
#                                                                                  Borrow
#----------------------------------------------------------------------------------------
def test_borrow_str():
    v = BorrowFactory.build()

    assert str(v) == 'Pasiskolinta 100'


def test_borrow_fields():
    assert Borrow._meta.get_field('date')
    assert Borrow._meta.get_field('name')
    assert Borrow._meta.get_field('price')
    assert Borrow._meta.get_field('returned')
    assert Borrow._meta.get_field('closed')
    assert Borrow._meta.get_field('account')
    assert Borrow._meta.get_field('user')
    assert Borrow._meta.get_field('remark')


def test_borrow_related():
    BorrowFactory()
    BorrowFactory(user=UserFactory(username='XXX'))

    actual = Borrow.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == 'Pasiskolinta 100'


def test_borrow_related_and_not_closed():
    BorrowFactory(name='N1', price=2, closed=False)
    BorrowFactory(name='N2', price=3, closed=True)

    actual = Borrow.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == 'Pasiskolinta 2'
    assert actual[0].name == 'N1'


def test_borrow_items():
    BorrowFactory()
    BorrowFactory(name='X1', user=UserFactory(username='XXX'))

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert str(actual[0]) == 'Pasiskolinta 100'


def test_borrow_year():
    BorrowFactory(name='N1', date=dt(1999, 2, 3))
    BorrowFactory(name='N2', date=dt(2999, 2, 3), price=2)

    actual = Borrow.objects.year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == 'Pasiskolinta 100'
    assert actual[0].name == 'N1'
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == Decimal('100')


def test_borrow_summary(borrow_fixture):
    expect = [{
        'id': 1,
        'title': 'A1',
        'borrow_past': Decimal('9'),
        'borrow_now': Decimal('3'),

    }, {
        'id': 2,
        'title': 'A2',
        'borrow_past': Decimal('0'),
        'borrow_now': Decimal('3.1'),
    }]

    actual = list(Borrow.objects.summary(1999).order_by('account__title'))

    assert expect == actual


def test_borrow_new_post_save():
    BorrowFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['balance'] == 100.0


def test_borrow_update_post_save():
    obj = BorrowFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['balance'] == 1.0


def test_borrow_post_delete():
    obj = BorrowFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0
    assert actual['balance'] == 0


def test_borrow_post_delete_with_update():
    BorrowFactory(price=1)

    obj = BorrowFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['balance'] == 1.0

    assert Borrow.objects.all().count() == 1


#----------------------------------------------------------------------------------------
#                                                                           Borrow Return
#----------------------------------------------------------------------------------------
def test_borrow_return_str():
    v = BorrowReturnFactory.build()

    assert str(v) == 'Grąžinau 5.0'


def test_borrow_return_fields():
    assert BorrowReturn._meta.get_field('date')
    assert BorrowReturn._meta.get_field('price')
    assert BorrowReturn._meta.get_field('account')
    assert BorrowReturn._meta.get_field('borrow')
    assert BorrowReturn._meta.get_field('remark')


def test_borrow_return_related():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')

    b1 = BorrowFactory(name='B1', price=1, user=u1)
    b2 = BorrowFactory(name='B2', price=2, user=u2)

    BorrowReturnFactory(borrow=b1, price=1.1)
    BorrowReturnFactory(borrow=b2, price=2.1)

    actual = BorrowReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžinau 1.1'


def test_borrow_return_items():
    BorrowReturnFactory()
    BorrowReturnFactory()

    actual = BorrowReturn.objects.items()

    assert actual.count() == 2


def test_borrow_return_year():
    BorrowReturnFactory()
    BorrowReturnFactory(date=date(1974, 1, 2))

    actual = BorrowReturn.objects.year(1999)

    assert actual.count() == 1


def test_borrow_return_summary(borrow_return_fixture):
    expect = [{
        'id': 1,
        'title': 'A1',
        'borrow_return_past': Decimal('8'),
        'borrow_return_now': Decimal('2'),

    }, {
        'id': 2,
        'title': 'A2',
        'borrow_return_past': Decimal('0'),
        'borrow_return_now': Decimal('1.6'),
    }]

    actual = list(BorrowReturn.objects.summary(1999).order_by('account__title'))

    assert expect == actual


def test_borrow_return_new_record_updates_borrow_tbl():
    BorrowReturnFactory()

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')


@patch('project.debts.models.super')
def test_borrow_return_new_record_updates_borrow_tbl_error_on_save(mck):
    mck.side_effect = TypeError

    try:
        BorrowReturnFactory()
    except:
        pass

    actual = Borrow.objects.items()

    assert actual[0].returned == Decimal('25')


def test_borrow_return_delete_record_updates_borrow_tbl():
    obj = BorrowReturnFactory()

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')

    obj.delete()

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('25')


def test_borrow_return_delete_record_updates_borrow_tbl_error_on_save():
    obj = BorrowReturnFactory()

    actual = Borrow.objects.items()

    assert actual[0].returned == Decimal('30')

    with patch('project.debts.models.super') as mck:
        mck.side_effect = TypeError

        try:
            obj.delete()
        except:
            pass

    actual = Borrow.objects.items()

    assert actual[0].returned == Decimal('30')


def test_borrow_return_new_post_save():
    BorrowReturnFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]
    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 5.0
    assert actual['balance'] == 95.0


def test_borrow_return_update_post_save():
    obj = BorrowReturnFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == 99.0


def test_borrow_return_post_delete():
    obj = BorrowReturnFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 0
    assert actual['balance'] == 100.0


def test_borrow_return_post_delete_with_update():
    b = BorrowFactory()
    BorrowReturnFactory(borrow=b, price=1)

    obj = BorrowReturnFactory(borrow=b)
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == 99.0

    assert Borrow.objects.all().count() == 1


#----------------------------------------------------------------------------------------
#                                                                                    Lent
#----------------------------------------------------------------------------------------
def test_lent_str():
    v = LentFactory.build()

    assert str(v) == 'Paskolinau 100.0'


def test_lent_fields():
    assert Lent._meta.get_field('date')
    assert Lent._meta.get_field('name')
    assert Lent._meta.get_field('price')
    assert Lent._meta.get_field('returned')
    assert Lent._meta.get_field('closed')
    assert Lent._meta.get_field('account')
    assert Lent._meta.get_field('user')
    assert Lent._meta.get_field('remark')


def test_lent_related():
    LentFactory()
    LentFactory(user=UserFactory(username='XXX'))

    actual = Lent.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == 'Paskolinau 100.0'


def test_lent_related_and_not_closed():
    LentFactory(name='N1', price=2, closed=False)
    LentFactory(name='N2', price=3, closed=True)

    actual = Lent.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == 'Paskolinau 2.0'
    assert actual[0].name == 'N1'


def test_lent_items():
    LentFactory()
    LentFactory(name='X1', user=UserFactory(username='XXX'))

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert str(actual[0]) == 'Paskolinau 100.0'


def test_lent_year():
    LentFactory(name='N1', date=dt(1999, 2, 3))
    LentFactory(name='N2', date=dt(2999, 2, 3), price=2)

    actual = Lent.objects.year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == 'Paskolinau 100.0'
    assert actual[0].name == 'N1'
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == Decimal('100')


def test_lent_summary(lent_fixture):
    expect = [{
        'id': 1,
        'title': 'A1',
        'lent_past': Decimal('9'),
        'lent_now': Decimal('3'),

    }, {
        'id': 2,
        'title': 'A2',
        'lent_past': Decimal('0'),
        'lent_now': Decimal('3.1'),
    }]

    actual = list(Lent.objects.summary(1999).order_by('account__title'))

    assert expect == actual


def test_lent_new_post_save():
    LentFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -100.0


def test_lent_update_post_save():
    obj = LentFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == -1.0


def test_lent_post_delete():
    obj = LentFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0
    assert actual['expenses'] == 0
    assert actual['balance'] == 0


def test_lent_post_delete_with_update():
    LentFactory(price=1)

    obj = LentFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == -1.0

    assert Lent.objects.all().count() == 1


#----------------------------------------------------------------------------------------
#                                                                           Lent Return
#----------------------------------------------------------------------------------------
def test_lent_return_str():
    v = LentReturnFactory.build()

    assert str(v) == 'Grąžino 5.0'

def test_lent_return_fields():
    assert LentReturn._meta.get_field('date')
    assert LentReturn._meta.get_field('price')
    assert LentReturn._meta.get_field('account')
    assert LentReturn._meta.get_field('lent')
    assert LentReturn._meta.get_field('remark')


def test_lent_return_related():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')

    b1 = LentFactory(name='B1', price=1, user=u1)
    b2 = LentFactory(name='B2', price=2, user=u2)

    LentReturnFactory(lent=b1, price=1.1)
    LentReturnFactory(lent=b2, price=2.1)

    actual = LentReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžino 1.1'


def test_lent_return_items():
    LentReturnFactory()
    LentReturnFactory()

    actual = LentReturn.objects.items()

    assert actual.count() == 2


def test_lent_return_year():
    LentReturnFactory()
    LentReturnFactory(date=date(1974, 1, 2))

    actual = LentReturn.objects.year(1999)

    assert actual.count() == 1


def test_lent_return_summary(lent_return_fixture):
    expect = [{
        'id': 1,
        'title': 'A1',
        'lent_return_past': Decimal('8'),
        'lent_return_now': Decimal('2'),

    }, {
        'id': 2,
        'title': 'A2',
        'lent_return_past': Decimal('0'),
        'lent_return_now': Decimal('1.6'),
    }]

    actual = list(
        LentReturn
        .objects
        .summary(1999)
        .order_by('account__title')
    )

    assert expect == actual


def test_lent_return_new_record_updates_lent_tbl():
    LentReturnFactory()

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')


@patch('project.debts.models.super')
def test_lent_return_new_record_updates_lent_tbl_error_on_save(mck):
    mck.side_effect = TypeError

    try:
        LentReturnFactory()
    except:
        pass

    actual = Lent.objects.items()

    assert actual[0].returned == Decimal('25')


def test_lent_return_delete_record_updates_lent_tbl():
    obj = LentReturnFactory()

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')

    obj.delete()

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('25')


def test_lent_return_delete_record_updates_lent_tbl_error_on_save():
    obj = LentReturnFactory()

    actual = Lent.objects.items()

    assert actual[0].returned == Decimal('30')

    with patch('project.debts.models.super') as mck:
        mck.side_effect = TypeError

        try:
            obj.delete()
        except:
            pass

    actual = Lent.objects.items()

    assert actual[0].returned == Decimal('30')


def test_lent_return_new_post_save():
    LentReturnFactory()

    actual = AccountBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]
    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 5.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -95.0


def test_lent_return_update_post_save():
    obj = LentReturnFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -99.0


def test_lent_return_post_delete():
    obj = LentReturnFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -100.0


def test_lent_return_post_delete_with_update():
    b = LentFactory()
    LentReturnFactory(lent=b, price=1)

    obj = LentReturnFactory(lent=b)
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -99.0

    assert Lent.objects.all().count() == 1
