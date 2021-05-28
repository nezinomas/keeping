from datetime import date
from datetime import date as dt
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...users.factories import UserFactory
from ..factories import BorrowFactory
from ..models import Borrow

pytestmark = pytest.mark.django_db


#----------------------------------------------------------------------------------------
#                                                                                  Borrow
#----------------------------------------------------------------------------------------
def test_borrow_str():
    v = BorrowFactory.build()

    assert str(v) == 'Pasiskolinta 100'


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
