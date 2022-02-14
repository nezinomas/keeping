from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

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


def test_pension_type_items_user(main_user, second_user):
    PensionTypeFactory(title='T1', journal=main_user.journal)
    PensionTypeFactory(title='T2', journal=second_user.journal)

    actual = PensionType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


@pytest.mark.xfail
def test_pension_type_unique_for_journal(main_user):
    PensionType.objects.create(title='T1', journal=main_user.journal)
    PensionType.objects.create(title='T1', journal=main_user.journal)


def test_pension_type_unique_for_journals(main_user, second_user):
    PensionType.objects.create(title='T1', journal=main_user.journal)
    PensionType.objects.create(title='T1', journal=second_user.journal)


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_str():
    p = PensionFactory.build()

    assert str(p) == '1999-01-01: PensionType'


def test_pension_object():
    p = PensionFactory()

    actual = Pension.objects.get(pk=p.id)

    assert actual.date == date(1999, 1, 1)
    assert actual.price == Decimal(100)
    assert actual.fee == pytest.approx(Decimal(1.01))
    assert actual.remark == 'remark'
    assert actual.pension_type.title == 'PensionType'


def test_pension_related(main_user, second_user):
    t1 = PensionTypeFactory(title='T1', journal=main_user.journal)
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
    PensionFactory(price=1)

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'PensionType'

    assert round(actual['incomes'], 2) == 1.0
    assert round(actual['fee'], 2) == 1.01
    assert round(actual['invested'], 2) == 0.0


def test_pension_post_save_update():
    u = PensionFactory()

    obj_update = Pension.objects.get(pk=u.pk)
    obj_update.price = 1
    obj_update.save()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'PensionType'

    assert round(actual['incomes'], 2) == 1.0
    assert round(actual['fee'], 2) == 1.01
    assert round(actual['invested'], 2) == 0.0


def test_pension_post_save_first_record():
    PensionFactory()

    PensionBalance.objects.all().delete()

    PensionFactory()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'PensionType'

    assert round(actual['incomes'], 2) == 200.0
    assert round(actual['fee'], 2) == 2.02
    assert round(actual['invested'], 2) == 197.98


def test_pension_post_save_different_types():
    t1 = PensionTypeFactory(title='1')
    t2 = PensionTypeFactory(title='2')

    PensionFactory(pension_type=t1, price=150, fee=15)
    PensionFactory(pension_type=t2, price=250, fee=25)

    actual = Pension.objects.all()
    assert actual.count() == 2

    actual = PensionBalance.objects.all()
    assert actual.count() == 2

    actual = PensionBalance.objects.get(year=1999, pension_type_id=t1.pk)
    assert actual.incomes == 150.0
    assert actual.fee == 15.0
    assert actual.invested == 135.0

    actual = PensionBalance.objects.get(year=1999, pension_type_id=t2.pk)
    assert actual.incomes == 250.0
    assert actual.fee == 25.0
    assert actual.invested == 225.0


def test_pension_post_save_update_nothing_changed():
    _p = PensionTypeFactory()
    obj = PensionFactory(pension_type=_p, price=1, fee=0.25)

    obj_update = Pension.objects.get(pk=obj.pk)
    obj_update.save()

    actual = PensionBalance.objects.get(pension_type_id=_p.pk, year=1999)
    assert actual.pension_type.title == _p.title
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fee == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_pension_post_save_update_changed_pension_type():
    _p = PensionTypeFactory(title='P')
    _p_new = PensionTypeFactory(title='P_New')

    obj = PensionFactory(pension_type=_p, price=1, fee=0.25)

    actual = PensionBalance.objects.get(pension_type_id=_p.pk, year=1999)
    assert actual.pension_type.title == 'P'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fee == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0

    obj_update = Pension.objects.get(pk=obj.pk)
    obj_update.pension_type = _p_new
    obj_update.save()

    fail = False
    try:
        actual = PensionBalance.objects.get(pension_type_id=_p.pk, year=1999)
    except PensionBalance.DoesNotExist:
        fail = True

    assert fail

    actual = PensionBalance.objects.get(pension_type_id=_p_new.pk, year=1999)
    assert actual.pension_type.title == 'P_New'
    assert actual.past_amount == 0.0
    assert actual.past_fee == 0.0
    assert actual.fee == 0.25
    assert actual.invested == 0.75
    assert actual.incomes == 1.0


def test_pension_post_delete():
    d = PensionFactory(price=15)

    Pension.objects.get(pk=d.pk).delete()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'PensionType'
    assert round(actual[0]['incomes'], 2) == 0
    assert round(actual[0]['fee'], 2) == 0
    assert round(actual[0]['invested'], 2) == 0

    assert Pension.objects.all().count() == 0


def test_pension_post_delete_with_update():
    PensionFactory(price=1)

    obj = PensionFactory(price=15)
    Pension.objects.get(pk=obj.pk).delete()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'PensionType'
    assert round(actual[0]['incomes'], 2) == 1.0
    assert round(actual[0]['fee'], 2) == 1.01
    assert round(actual[0]['invested'], 2) == 0.0

    assert Pension.objects.all().count() == 1


def test_pension_update_post_save_count_queries(django_assert_max_num_queries):
    PensionFactory()

    obj = Pension.objects.first()
    with django_assert_max_num_queries(4):
        obj.price = Decimal('2')
        obj.save()

    actual = PensionBalance.objects.last()
    assert actual.incomes == Decimal('2')


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
def test_pension_balance_init():
    actual = PensionBalanceFactory.build()

    assert str(actual.pension_type) == 'PensionType'

    assert actual.past_amount == 2.0
    assert actual.past_fee == 2.1
    assert actual.fee == 2.2
    assert actual.invested == 2.3
    assert actual.incomes == 2.4
    assert actual.market_value == 2.5
    assert actual.profit_incomes_proc == 2.6
    assert actual.profit_incomes_sum == 2.7
    assert actual.profit_invested_proc == 2.8
    assert actual.profit_invested_sum == 2.9


def test_pension_balance_str():
    actual = PensionBalanceFactory.build()

    assert str(actual) == 'PensionType'


def test_pension_balance_related_for_user(main_user, second_user):
    p1 = PensionTypeFactory(title='P1', journal=main_user.journal)
    p2 = PensionTypeFactory(title='P2', journal=second_user.journal)

    PensionFactory(pension_type=p1)
    PensionFactory(pension_type=p2)

    actual = PensionBalance.objects.related()

    assert len(actual) == 1
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


@freeze_time('1999-1-1')
def test_sum_by_year():
    PensionFactory(price=1)
    PensionFactory(price=2)

    actual = list(PensionBalance.objects.sum_by_year())

    assert actual == [{'year': 1999, 'invested': 3.0, 'profit': -3.0}]
