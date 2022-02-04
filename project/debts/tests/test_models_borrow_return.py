from datetime import date as dt
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...incomes.factories import IncomeFactory
from ..factories import BorrowFactory, BorrowReturnFactory
from ..models import Borrow, BorrowReturn

pytestmark = pytest.mark.django_db


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

    actual = list(
        BorrowReturn
        .objects
        .summary(1999)
        .order_by('account__title')
    )

    assert expect == actual


def test_borrow_return_new_record_updates_borrow_tbl():
    BorrowReturnFactory()

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('30')


def test_borrow_return_update():
    obj = BorrowReturnFactory()

    actual = Borrow.objects.items()
    assert actual[0].returned == Decimal('30')

    obj.price = Decimal('20')
    obj.save()

    assert BorrowReturn.objects.items().count() == 1

    actual = Borrow.objects.items()
    assert actual[0].returned == Decimal('45')


def test_borrow_return_new_record_updates_borrow_tbl_empty_returned_field():
    BorrowReturnFactory(borrow=BorrowFactory(returned=None))

    actual = Borrow.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('5')


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
    obj_update = BorrowReturn.objects.get(pk=obj.pk)
    obj_update.price = 1
    obj_update.save()

    actual = AccountBalance.objects.year(1999)

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['incomes'] == 1.0
    assert actual['expenses'] == 100.0
    assert actual['balance'] == -99.0


def test_borrow_return_post_save_first_record():
    l = BorrowFactory(price=2)

    IncomeFactory(date=dt(1998, 1, 1), price=5)

    # truncate AccountBalance table
    AccountBalance.objects.all().delete()

    BorrowReturnFactory(date=dt(1999, 1, 1), borrow=l, price=1)

    actual = AccountBalance.objects.items()

    assert actual[0].year == 1998
    assert actual[0].past == 0.0
    assert actual[0].incomes == 5.0
    assert actual[0].expenses == 0.0
    assert actual[0].balance == 5.0
    assert actual[0].delta == -5.0

    assert actual[1].year == 1999
    assert actual[1].past == 5.0
    assert actual[1].incomes == 1.0
    assert actual[1].expenses == 2.0
    assert actual[1].balance == 4.0
    assert actual[1].delta == -4.0


def test_borrow_return_post_delete():
    obj = BorrowReturnFactory()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 5.0
    assert actual.expenses == 100.0
    assert actual.balance == -95.0

    BorrowReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 0.0
    assert actual.expenses == 100.0
    assert actual.balance == -100.0


def test_borrow_return_post_delete_with_updt():
    b = BorrowFactory()
    BorrowReturnFactory(borrow=b, price=1)

    obj = BorrowReturnFactory(borrow=b)

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 6.0
    assert actual.expenses == 100.0
    assert actual.balance == -94.0

    BorrowReturn.objects.get(pk=obj.pk).delete()

    actual = AccountBalance.objects.last()
    assert actual.account.title == 'Account1'
    assert actual.incomes == 1.0
    assert actual.expenses == 100.0
    assert actual.balance == -99.0


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


def test_borrow_return_autoclose():
    BorrowReturnFactory(price=75)

    actual = Borrow.objects.first()

    assert actual.returned == Decimal('100')
    assert actual.closed


def test_borrow_return_incomes():
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

    actual = BorrowReturn.objects.incomes()

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
