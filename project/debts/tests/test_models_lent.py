from datetime import date as dt
from decimal import Decimal

import pytest

from ...accounts.models import AccountBalance
from ..factories import LentFactory
from ..models import Lent

pytestmark = pytest.mark.django_db


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
