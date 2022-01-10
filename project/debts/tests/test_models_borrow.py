from datetime import date as dt
from decimal import Decimal

import pytest

from ...accounts.models import AccountBalance
from ..factories import BorrowFactory
from ..models import Borrow

pytestmark = pytest.mark.django_db


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