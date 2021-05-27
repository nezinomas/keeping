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
#                                                                         pytest fixtures
#----------------------------------------------------------------------------------------
@pytest.fixture
def _borrow_fixture():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    BorrowFactory(date=dt(1999, 1, 2), price=1, account=a1)
    BorrowFactory(date=dt(1999, 2, 3), price=2, account=a1)
    BorrowFactory(date=dt(1999, 3, 4), price=3.1, account=a2)

    BorrowFactory(date=dt(1974, 1, 2), price=4, account=a1)
    BorrowFactory(date=dt(1974, 2, 3), price=5, account=a1)


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


def test_borrow_summary(_borrow_fixture):
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
