from datetime import date as dt
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.models import AccountBalance
from ..factories import (BorrowFactory, BorrowReturnFactory, LentFactory,
                         LentReturnFactory)
from ..models import Borrow, BorrowReturn, Lent, LentReturn

pytestmark = pytest.mark.django_db


#----------------------------------------------------------------------------------------
#                                                                                  Borrow
#----------------------------------------------------------------------------------------
def test_borrow_str():
    v = BorrowFactory.build(name='X')

    assert str(v) == 'X'


def test_borrow_fields():
    assert Borrow._meta.get_field('date')
    assert Borrow._meta.get_field('name')
    assert Borrow._meta.get_field('price')
    assert Borrow._meta.get_field('returned')
    assert Borrow._meta.get_field('closed')
    assert Borrow._meta.get_field('account')
    assert Borrow._meta.get_field('journal')
    assert Borrow._meta.get_field('remark')


def test_borrow_related(main_user, second_user):
    o = BorrowFactory(journal=main_user.journal)
    BorrowFactory(journal=second_user.journal)

    actual = Borrow.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == str(o)


def test_borrow_related_queries(django_assert_num_queries):
    BorrowFactory()
    BorrowFactory()

    with django_assert_num_queries(1):
        a = [x.account.title for x in list(Borrow.objects.related())]


def test_borrow_sort():
    o1 = BorrowFactory(date=dt(1999, 1, 2))
    o2 = BorrowFactory(date=dt(1999, 12, 13))

    actual = Borrow.objects.related()

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


def test_borrow_items(main_user, second_user):
    o = BorrowFactory(journal=main_user.journal)
    BorrowFactory(name='X1', journal=second_user.journal)

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert str(actual[0]) == str(o)


def test_borrow_year():
    o = BorrowFactory(name='N1', date=dt(1999, 2, 3))
    BorrowFactory(name='N2', date=dt(2999, 2, 3), price=2)

    actual = Borrow.objects.year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == str(o)
    assert actual[0].name == o.name
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == Decimal('100')


def test_borrow_year_and_not_closed():
    o1 = BorrowFactory(date=dt(1974, 1, 1), closed=False)
    BorrowFactory(date=dt(1974, 12, 1), closed=True)
    o2 = BorrowFactory(date=dt(1999, 1, 1), closed=False)
    o3 = BorrowFactory(date=dt(1999, 12, 1), closed=True)

    actual = Borrow.objects.year(1999)

    assert actual.count() == 3

    assert actual[0].date == o3.date
    assert actual[1].date == o2.date
    assert actual[2].date == o1.date


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
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -100.0


def test_borrow_update_post_save():
    obj = BorrowFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == -1.0


def test_borrow_post_delete():
    obj = BorrowFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0
    assert actual['balance'] == 0


def test_borrow_post_delete_with_updt():
    BorrowFactory(price=1)

    obj = BorrowFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == -1.0

    assert Borrow.objects.all().count() == 1


def test_borrow_unique_users(main_user, second_user):
    BorrowFactory(name='T1', journal=main_user.journal)
    BorrowFactory(name='T1', journal=second_user.journal)


def test_borrow_sum_all_months():
    BorrowFactory(date=dt(1999, 1, 1), price=1, returned=0.5)
    BorrowFactory(date=dt(1999, 1, 2), price=2, returned=0.5)
    BorrowFactory(date=dt(1999, 2, 1), price=4, returned=1)
    BorrowFactory(date=dt(1999, 2, 2), price=1, returned=0.5)
    BorrowFactory(date=dt(1999, 1, 1), closed=True)
    BorrowFactory(date=dt(1974, 1, 1))

    expect = [
        {'date': dt(1999, 1, 1), 'sum_debt': Decimal('3'), 'sum_return': Decimal('1')},
        {'date': dt(1999, 2, 1), 'sum_debt': Decimal('5'), 'sum_return': Decimal('1.5')},
    ]

    actual = list(Borrow.objects.sum_by_month(1999))

    assert expect == actual


def test_borrow_sum_all_months_ordering(second_user):
    BorrowFactory(date=dt(1999, 1, 1), price=1)
    BorrowFactory(date=dt(1999, 1, 2), price=2)
    BorrowFactory(date=dt(1999, 1, 2), price=2, journal=second_user.journal)
    BorrowFactory(date=dt(1999, 2, 1), price=4)
    BorrowFactory(date=dt(1999, 2, 2), price=1)
    BorrowFactory(date=dt(1999, 2, 2), price=6, journal=second_user.journal)

    actual = list(Borrow.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


def test_borrow_sum_all_not_closed():
    BorrowFactory(date=dt(1999, 1, 1), price=12, closed=True)
    BorrowFactory(date=dt(1999, 1, 1), price=1, returned=0.5)
    BorrowFactory(date=dt(1999, 1, 2), price=1, returned=0.5)
    BorrowFactory(date=dt(1974, 1, 2), price=3, returned=2)

    expect = {'borrow': Decimal('5'), 'borrow_return': Decimal('3')}

    actual = Borrow.objects.sum_all()

    assert expect == actual


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


def test_borrow_return_related(main_user, second_user):
    b1 = BorrowFactory(name='B1', price=1, journal=main_user.journal)
    b2 = BorrowFactory(name='B2', price=2, journal=second_user.journal)

    BorrowReturnFactory(borrow=b1, price=1.1)
    BorrowReturnFactory(borrow=b2, price=2.1)

    actual = BorrowReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžinau 1.1'


def test_borrow_return_related_queries(django_assert_num_queries):
    BorrowReturnFactory()
    BorrowReturnFactory()

    with django_assert_num_queries(1):
        a = [x.account.title for x in list(BorrowReturn.objects.related())]


def test_borrow_return_sort():
    o1 = BorrowReturnFactory(date=dt(1999, 1, 2))
    o2 = BorrowReturnFactory(date=dt(1999, 12, 13))

    actual = BorrowReturn.objects.related()

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


def test_borrow_return_items():
    BorrowReturnFactory()
    BorrowReturnFactory()

    actual = BorrowReturn.objects.items()

    assert actual.count() == 2


def test_borrow_return_year():
    BorrowReturnFactory()
    BorrowReturnFactory(date=dt(1974, 1, 2))

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


def test_borrow_return_new_record_updates_borrow_tbl_empty_returned_field():
    BorrowReturnFactory(borrow=BorrowFactory(returned=None))

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('5')


@patch('project.debts.models.super')
def test_borrow_return_new_record_updates_borrow_tbl_error_on_save(mck):
    mck.side_effect = TypeError

    try:
        BorrowReturnFactory()
    except:
        pass

    actual = Borrow.objects.items()

    assert actual[0].returned == Decimal('25')


@patch('project.debts.models.Borrow.objects.get')
def test_borrow_return_new_record_updates_borrow_tbl_error_on_save_parent(mck):
    mck.side_effect = TypeError

    try:
        BorrowReturnFactory()
    except:
        pass

    actual = Borrow.objects.items()
    assert actual[0].returned == Decimal('25')

    actual = BorrowReturn.objects.all()
    assert actual.count() == 0


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
    assert actual['incomes'] == 5.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -95.0


def test_borrow_return_update_post_save():
    obj = BorrowReturnFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -99.0


def test_borrow_return_post_delete():
    obj = BorrowReturnFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -100.0


def test_borrow_return_post_delete_with_updt():
    b = BorrowFactory()
    BorrowReturnFactory(borrow=b, price=1)

    obj = BorrowReturnFactory(borrow=b)
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -99.0

    assert Borrow.objects.all().count() == 1


def test_borrow_return_sum_all_months():
    BorrowReturnFactory(date=dt(1999, 1, 1), price=1)
    BorrowReturnFactory(date=dt(1999, 1, 2), price=2)
    BorrowReturnFactory(date=dt(1999, 2, 1), price=4)
    BorrowReturnFactory(date=dt(1999, 2, 2), price=1)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')},
        {'date': dt(1999, 2, 1), 'sum': Decimal('5')},
    ]

    actual = list(BorrowReturn.objects.sum_by_month(1999))

    assert expect == actual


def test_borrow_return_sum_all_months_ordering():
    BorrowReturnFactory(date=dt(1999, 1, 1), price=1)
    BorrowReturnFactory(date=dt(1999, 1, 2), price=2)
    BorrowReturnFactory(date=dt(1999, 2, 1), price=4)
    BorrowReturnFactory(date=dt(1999, 2, 2), price=1)

    actual = list(BorrowReturn.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


def test_borrow_return_sum_one_month():
    BorrowReturnFactory(date=dt(1999, 1, 1), price=1)
    BorrowReturnFactory(date=dt(1999, 1, 2), price=2)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')}
    ]

    actual = list(BorrowReturn.objects.sum_by_month(1999, 1))

    assert len(expect) == 1
    assert expect == actual


#----------------------------------------------------------------------------------------
#                                                                                    Lent
#----------------------------------------------------------------------------------------
def test_lent_str():
    v = LentFactory.build(name='X')

    assert str(v) == 'X'


def test_lent_fields():
    assert Lent._meta.get_field('date')
    assert Lent._meta.get_field('name')
    assert Lent._meta.get_field('price')
    assert Lent._meta.get_field('returned')
    assert Lent._meta.get_field('closed')
    assert Lent._meta.get_field('account')
    assert Lent._meta.get_field('journal')
    assert Lent._meta.get_field('remark')


def test_lent_related(second_user):
    o = LentFactory()
    LentFactory(journal=second_user.journal)

    actual = Lent.objects.related()

    assert len(actual) == 1
    assert str(actual[0]) == str(o)


def test_lent_related_queries(django_assert_num_queries):
    LentFactory()
    LentFactory()

    with django_assert_num_queries(1):
        a = [x.account.title for x in list(Lent.objects.related())]


def test_lent_sort():
    o1 = LentFactory(date=dt(1999, 1, 2))
    o2 = LentFactory(date=dt(1999, 12, 13))

    actual = Lent.objects.related()

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


def test_lent_items(second_user):
    o = LentFactory()
    LentFactory(name='X1', journal=second_user.journal)

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert str(actual[0]) == str(o)


def test_lent_year():
    o = LentFactory(name='N1', date=dt(1999, 2, 3))
    LentFactory(name='N2', date=dt(2999, 2, 3), price=2)

    actual = Lent.objects.year(1999)

    assert actual.count() == 1
    assert str(actual[0]) == str(o)
    assert actual[0].name == o.name
    assert actual[0].date == dt(1999, 2, 3)
    assert actual[0].price == Decimal('100')


def test_lent_year_and_not_closed():
    o1 = LentFactory(date=dt(1974, 1, 1), closed=False)
    LentFactory(date=dt(1974, 12, 1), closed=True)
    o2 = LentFactory(date=dt(1999, 1, 1), closed=False)
    o3 = LentFactory(date=dt(1999, 12, 1), closed=True)

    actual = Lent.objects.year(1999)

    assert actual.count() == 3

    assert actual[0].date == o3.date
    assert actual[1].date == o2.date
    assert actual[2].date == o1.date


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
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 100.0


def test_lent_update_post_save():
    obj = LentFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0


def test_lent_post_delete():
    obj = LentFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 0
    assert actual['expenses'] == 0
    assert actual['balance'] == 0


def test_lent_post_delete_with_updt():
    LentFactory(price=1)

    obj = LentFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 1.0

    assert Lent.objects.all().count() == 1


def test_lent_unique_users(main_user, second_user):
    LentFactory(name='T1', journal=main_user.journal)
    LentFactory(name='T1', journal=second_user.journal)


def test_lent_sum_all_months():
    LentFactory(date=dt(1999, 1, 1), price=1, returned=0.5)
    LentFactory(date=dt(1999, 1, 2), price=2, returned=0.5)
    LentFactory(date=dt(1999, 2, 1), price=4, returned=1)
    LentFactory(date=dt(1999, 2, 2), price=1, returned=0.5)
    LentFactory(date=dt(1999, 1, 1), closed=True)
    LentFactory(date=dt(1974, 1, 1))

    expect = [
        {'date': dt(1999, 1, 1), 'sum_debt': Decimal('3'), 'sum_return': Decimal('1')},
        {'date': dt(1999, 2, 1), 'sum_debt': Decimal('5'), 'sum_return': Decimal('1.5')},
    ]

    actual = list(Lent.objects.sum_by_month(1999))

    assert expect == actual


def test_lent_sum_all_months_ordering(second_user):
    LentFactory(date=dt(1999, 1, 1), price=1)
    LentFactory(date=dt(1999, 1, 2), price=2)
    LentFactory(date=dt(1999, 1, 2), price=2, journal=second_user.journal)
    LentFactory(date=dt(1999, 2, 1), price=4)
    LentFactory(date=dt(1999, 2, 2), price=1)
    LentFactory(date=dt(1999, 2, 2), price=6, journal=second_user.journal)

    actual = list(Lent.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


def test_lent_sum_all_not_closed():
    LentFactory(date=dt(1999, 1, 1), price=12, closed=True)
    LentFactory(date=dt(1999, 1, 1), price=1, returned=0.5)
    LentFactory(date=dt(1999, 1, 2), price=1, returned=0.5)
    LentFactory(date=dt(1974, 1, 2), price=3, returned=2)

    expect = {'lent': Decimal('5'), 'lent_return': Decimal('3')}

    actual = Lent.objects.sum_all()

    assert expect == actual


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


def test_lent_return_related(main_user, second_user):
    b1 = LentFactory(name='B1', price=1, journal=main_user.journal)
    b2 = LentFactory(name='B2', price=2, journal=second_user.journal)

    LentReturnFactory(lent=b1, price=1.1)
    LentReturnFactory(lent=b2, price=2.1)

    actual = LentReturn.objects.related()

    assert actual.count() == 1
    assert str(actual[0]) == 'Grąžino 1.1'


def test_lent_return_related_queries(django_assert_num_queries):
    LentReturnFactory()
    LentReturnFactory()

    with django_assert_num_queries(1):
        a = [x.account.title for x in list(LentReturn.objects.related())]


def test_lent_return_sort():
    o1 = LentReturnFactory(date=dt(1999, 1, 2))
    o2 = LentReturnFactory(date=dt(1999, 12, 13))

    actual = LentReturn.objects.related()

    assert actual[0].date == o2.date
    assert actual[1].date == o1.date


def test_lent_return_items():
    LentReturnFactory()
    LentReturnFactory()

    actual = LentReturn.objects.items()

    assert actual.count() == 2


def test_lent_return_year():
    LentReturnFactory()
    LentReturnFactory(date=dt(1974, 1, 2))

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


def test_lent_return_new_record_updates_lent_tbl_empty_returned_field():
    LentReturnFactory(lent=LentFactory(returned=None))

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('5')


@patch('project.debts.models.super')
def test_lent_return_new_record_updates_lent_tbl_error_on_save(mck):
    mck.side_effect = TypeError

    try:
        LentReturnFactory()
    except:
        pass

    actual = Lent.objects.items()

    assert actual[0].returned == Decimal('25')


@patch('project.debts.models.Lent.objects.get')
def test_lent_return_new_record_updates_lent_tbl_error_on_save_parent(mck):
    mck.side_effect = TypeError

    try:
        LentReturnFactory()
    except:
        pass

    actual = Lent.objects.items()
    assert actual[0].returned == Decimal('25')

    actual = LentReturn.objects.all()
    assert actual.count() == 0


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
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 5.0
    assert actual['balance'] == 95.0


def test_lent_return_update_post_save():
    obj = LentReturnFactory()

    # update object
    obj.price = 1
    obj.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == 99.0


def test_lent_return_post_delete():
    obj = LentReturnFactory()
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 0.0
    assert actual['balance'] == 100.0


def test_lent_return_post_delete_with_updt():
    b = LentFactory()
    LentReturnFactory(lent=b, price=1)

    obj = LentReturnFactory(lent=b)
    obj.delete()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 100.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == 99.0

    assert Lent.objects.all().count() == 1


def test_lent_return_sum_all_months():
    LentReturnFactory(date=dt(1999, 1, 1), price=1)
    LentReturnFactory(date=dt(1999, 1, 2), price=2)
    LentReturnFactory(date=dt(1999, 2, 1), price=4)
    LentReturnFactory(date=dt(1999, 2, 2), price=1)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')},
        {'date': dt(1999, 2, 1), 'sum': Decimal('5')},
    ]

    actual = list(LentReturn.objects.sum_by_month(1999))

    assert expect == actual


def test_lent_return_sum_all_months_ordering():
    LentReturnFactory(date=dt(1999, 1, 1), price=1)
    LentReturnFactory(date=dt(1999, 1, 2), price=2)
    LentReturnFactory(date=dt(1999, 2, 1), price=4)
    LentReturnFactory(date=dt(1999, 2, 2), price=1)

    actual = list(LentReturn.objects.sum_by_month(1999))

    assert actual[0]['date'] == dt(1999, 1, 1)
    assert actual[1]['date'] == dt(1999, 2, 1)


def test_lent_return_sum_one_month():
    LentReturnFactory(date=dt(1999, 1, 1), price=1)
    LentReturnFactory(date=dt(1999, 1, 2), price=2)

    expect = [
        {'date': dt(1999, 1, 1), 'sum': Decimal('3')}
    ]

    actual = list(LentReturn.objects.sum_by_month(1999, 1))

    assert len(expect) == 1
    assert expect == actual
