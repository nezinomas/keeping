from datetime import date

import pytest
import time_machine
from django.urls import reverse

from ..factories import (PensionBalanceFactory, PensionFactory,
                         PensionTypeFactory)
from ..models import Pension, PensionBalance, PensionType

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  PensionType
# ----------------------------------------------------------------------------
def test_pension_type_str():
    p = PensionTypeFactory.build()

    assert str(p) == 'PensionType'


def test_pension_type_get_absolute_url():
    obj = PensionTypeFactory()

    assert obj.get_absolute_url() == reverse('pensions:type_update', kwargs={'pk': obj.pk})


def test_pension_type_items_user(second_user):
    PensionTypeFactory(title='T1')
    PensionTypeFactory(title='T2', journal=second_user.journal)

    actual = PensionType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


@pytest.mark.xfail
def test_pension_type_unique_for_journal():
    PensionType.objects.create(title='T1')
    PensionType.objects.create(title='T1')


def test_pension_type_unique_for_journals(main_user, second_user):
    PensionType.objects.create(title='T1', journal=main_user.journal)
    PensionType.objects.create(title='T1', journal=second_user.journal)


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_str():
    p = PensionFactory.build()

    assert str(p) == '1999-01-01: PensionType'


def test_pension_get_absolute_url():
    obj = PensionFactory()

    assert obj.get_absolute_url() == reverse('pensions:update', kwargs={'pk': obj.pk})


def test_pension_object():
    p = PensionFactory()

    actual = Pension.objects.get(pk=p.id)

    assert actual.date == date(1999, 1, 1)
    assert actual.price == 100
    assert actual.fee == 1
    assert actual.remark == 'remark'
    assert actual.pension_type.title == 'PensionType'


def test_pension_related(second_user):
    t1 = PensionTypeFactory(title='T1')
    t2 = PensionTypeFactory(title='T2', journal=second_user.journal)

    PensionFactory(pension_type=t1)
    PensionFactory(pension_type=t2)

    actual = Pension.objects.related()

    assert len(actual) == 1
    assert str(actual[0].pension_type) == 'T1'


def test_pension_items(pensions):
    assert len(Pension.objects.items()) == 4


def test_pension_items_query_count(pensions,
                                   django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(Pension.objects.items().values())


def test_pension_year(pensions):
    assert len(Pension.objects.year(1999)) == 2


def test_pension_year_query_count(pensions,
                                  django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(Pension.objects.year(1999).values())


def test_pension_post_save_new():
    PensionFactory()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.pension_type.title == 'PensionType'

    assert actual.incomes == 100
    assert actual.fee == 1
    assert actual.invested == 99


def test_pension_post_save_update():
    u = PensionFactory()

    obj_update = Pension.objects.get(pk=u.pk)
    obj_update.price = 101
    obj_update.save()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.pension_type.title == 'PensionType'

    assert actual.incomes == 101
    assert actual.fee == 1
    assert actual.invested == 100


def test_pension_post_save_first_record():
    PensionFactory()

    PensionBalance.objects.all().delete()

    PensionFactory()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual.pension_type.title == 'PensionType'

    assert actual.incomes == 200
    assert actual.fee == 2
    assert actual.invested == 198


def test_pension_post_save_different_types():
    t1 = PensionTypeFactory(title='1')
    t2 = PensionTypeFactory(title='2')

    PensionFactory(pension_type=t1, price=150, fee=15)
    PensionFactory(pension_type=t2, price=250, fee=25)

    actual = Pension.objects.all()
    assert actual.count() == 2

    actual = PensionBalance.objects.all()
    assert actual.count() == 4

    actual = PensionBalance.objects.get(year=1999, pension_type_id=t1.pk)
    assert actual.incomes == 150
    assert actual.fee == 15
    assert actual.invested == 135

    actual = PensionBalance.objects.get(year=1999, pension_type_id=t2.pk)
    assert actual.incomes == 250
    assert actual.fee == 25
    assert actual.invested == 225


def test_pension_post_save_update_nothing_changed():
    _p = PensionTypeFactory()
    obj = PensionFactory(pension_type=_p, price=10, fee=2)

    obj_update = Pension.objects.get(pk=obj.pk)
    obj_update.save()

    actual = PensionBalance.objects.get(pension_type_id=_p.pk, year=1999)
    assert actual.pension_type.title == _p.title
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.invested == 8
    assert actual.incomes == 10


def test_pension_post_save_update_changed_pension_type():
    _p = PensionTypeFactory(title='P')
    _p_new = PensionTypeFactory(title='P_New')

    obj = PensionFactory(pension_type=_p, price=10, fee=2)

    actual = PensionBalance.objects.get(pension_type_id=_p.pk, year=1999)
    assert actual.pension_type.title == 'P'
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.invested == 8
    assert actual.incomes == 10

    obj_update = Pension.objects.get(pk=obj.pk)
    obj_update.pension_type = _p_new
    obj_update.save()

    actual = PensionBalance.objects.filter(pension_type_id=_p.pk, year=1999)
    assert actual.count() == 0

    actual = PensionBalance.objects.get(pension_type_id=_p_new.pk, year=1999)
    assert actual.pension_type.title == 'P_New'
    assert actual.past_amount == 0
    assert actual.past_fee == 0
    assert actual.fee == 2
    assert actual.invested == 8
    assert actual.incomes == 10


def test_pension_post_delete():
    d = PensionFactory(price=15)

    Pension.objects.get(pk=d.pk).delete()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 0
    assert Pension.objects.all().count() == 0


def test_pension_post_delete_with_update():
    PensionFactory()

    obj = PensionFactory(price=15)
    Pension.objects.get(pk=obj.pk).delete()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0].pension_type.title == 'PensionType'
    assert round(actual[0].incomes, 2) == 100
    assert round(actual[0].fee, 2) == 1
    assert round(actual[0].invested, 2) == 99

    assert Pension.objects.all().count() == 1


def test_pension_update_post_save_count_queries(django_assert_max_num_queries):
    PensionFactory()

    obj = Pension.objects.first()
    with django_assert_max_num_queries(7):
        obj.price = 2
        obj.save()

    actual = PensionBalance.objects.last()
    assert actual.incomes == 2


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
def test_pension_balance_init():
    actual = PensionBalanceFactory.build()

    assert str(actual.pension_type) == 'PensionType'

    assert actual.past_amount == 20
    assert actual.past_fee == 21
    assert actual.fee == 22
    assert actual.invested == 23
    assert actual.incomes == 24
    assert actual.market_value == 25
    assert actual.profit_proc == 28
    assert actual.profit_sum == 29


def test_pension_balance_str():
    actual = PensionBalanceFactory.build()

    assert str(actual) == 'PensionType'


def test_pension_balance_related_for_user(second_user):
    p1 = PensionTypeFactory(title='P1')
    p2 = PensionTypeFactory(title='P2', journal=second_user.journal)

    PensionFactory(pension_type=p1)
    PensionFactory(pension_type=p2)

    actual = PensionBalance.objects.related()

    assert len(actual) == 2
    assert str(actual[0].pension_type) == 'P1'
    assert actual[0].pension_type.journal.title == 'bob Journal'
    assert actual[0].pension_type.journal.users.first().username == 'bob'


@pytest.mark.django_db
def test_pension_balance_items():
    PensionBalanceFactory(year=1998)
    PensionBalanceFactory(year=1999)
    PensionBalanceFactory(year=2000)

    actual = PensionBalance.objects.year(1999)

    assert len(actual) == 1


def test_pension_balance_queries(django_assert_num_queries):
    p1 = PensionTypeFactory(title='p1')
    p2 = PensionTypeFactory(title='p2')

    PensionBalanceFactory(pension_type=p1)
    PensionBalanceFactory(pension_type=p2)

    with django_assert_num_queries(1):
        list(PensionBalance.objects.items().values())


@time_machine.travel('1999-1-1')
def test_sum_by_year():
    PensionFactory(price=1, fee=0)
    PensionFactory(price=2, fee=0)

    actual = list(PensionBalance.objects.sum_by_year())

    assert actual == [
        {'year': 1999, 'invested': 3, 'profit': -3},
        {'year': 2000, 'invested': 3, 'profit': -3},
    ]
