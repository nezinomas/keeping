from datetime import date as dt
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.models import AccountBalance
from ..factories import LentFactory, LentReturnFactory
from ..models import Lent, LentReturn

pytestmark = pytest.mark.django_db


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

def test_lent_return_update():
    obj = LentReturnFactory()

    actual = Lent.objects.items()
    assert actual[0].returned == Decimal('30')

    obj.price = Decimal('20')
    obj.save()

    assert LentReturn.objects.items().count() == 1

    actual = Lent.objects.items()
    assert actual[0].returned == Decimal('45')


def test_lent_return_new_record_updates_lent_tbl_empty_returned_field():
    LentReturnFactory(lent=LentFactory(returned=None))

    actual = Lent.objects.items()

    assert actual.count() == 1
    assert actual[0].returned == Decimal('5')


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


def test_lent_return_autoclose():
    LentReturnFactory(price=75)

    actual = Lent.objects.first()

    assert actual.returned == Decimal('100')
    assert actual.closed