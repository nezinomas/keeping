from datetime import date
from decimal import Decimal

import pytest

from ...users.factories import UserFactory
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


def test_pension_type_items_user():
    PensionTypeFactory(title='T1', user=UserFactory())
    PensionTypeFactory(title='T2', user=UserFactory(username='u2'))

    actual = PensionType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


@pytest.mark.xfail
def test_pension_type_unique_for_user():
    PensionType.objects.create(title='T1', user=UserFactory())
    PensionType.objects.create(title='T1', user=UserFactory())


def test_pension_type_unique_for_users():
    PensionType.objects.create(title='T1', user=UserFactory(username='x'))
    PensionType.objects.create(title='T1', user=UserFactory(username='y'))


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


def test_pension_related():
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')
    t1 = PensionTypeFactory(title='T1', user=u1)
    t2 = PensionTypeFactory(title='T2', user=u2)

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


def test_pension_summary_query_count(pensions,
                                     django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        list(Pension.objects.summary(1999).values())


def test_pension_summary(pensions):
    expect = [{
        'id': 1,
        'title': 'PensionType',
        's_past': Decimal(3.5),
        's_now': Decimal(4.5),
        's_fee_past': Decimal(0.25),
        's_fee_now': Decimal(0.5),
    }]

    actual = list(Pension.objects.summary(1999))

    assert expect == actual


def test_pension_new_post_save():
    PensionFactory(price=1)

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'PensionType'

    assert round(actual['incomes'], 2) == 1.0
    assert round(actual['fees'], 2) == 1.01
    assert round(actual['invested'], 2) == -0.01


def test_pension_update_post_save():
    u = PensionFactory()
    u.price = 1
    u.save()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'PensionType'

    assert round(actual['incomes'], 2) == 1.0
    assert round(actual['fees'], 2) == 1.01
    assert round(actual['invested'], 2) == -0.01


def test_pension_post_delete():
    d = PensionFactory(price=15)
    d.delete()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'PensionType'
    assert round(actual[0]['incomes'], 2) == 0
    assert round(actual[0]['fees'], 2) == 0
    assert round(actual[0]['invested'], 2) == 0

    assert Pension.objects.all().count() == 0


def test_pension_post_delete_with_update():
    PensionFactory(price=1)

    d = PensionFactory(price=15)
    d.delete()

    actual = PensionBalance.objects.year(1999)

    assert actual.count() == 1
    assert actual[0]['title'] == 'PensionType'
    assert round(actual[0]['incomes'], 2) == 1.0
    assert round(actual[0]['fees'], 2) == 1.01
    assert round(actual[0]['invested'], 2) == -0.01

    assert Pension.objects.all().count() == 1


def test_pension_new_post_save_count_queries(django_assert_max_num_queries):
    PensionTypeFactory()

    assert PensionBalance.objects.all().count() == 0

    with django_assert_max_num_queries(13):
        PensionFactory()


def test_pension_update_post_save_count_queries(django_assert_max_num_queries):
    PensionBalanceFactory()

    assert PensionBalance.objects.all().count() == 1

    with django_assert_max_num_queries(11):
        PensionFactory()


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
def test_pension_balance_init():
    actual = PensionBalanceFactory.build()

    assert str(actual.pension_type) == 'PensionType'

    assert actual.past_amount == 2.0
    assert actual.past_fee == 2.1
    assert actual.fees == 2.2
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


def test_pension_balance_related_for_user():
    p1 = PensionTypeFactory(title='P1')
    p2 = PensionTypeFactory(title='P2', user=UserFactory(username='XXX'))

    PensionBalanceFactory(pension_type=p1)
    PensionBalanceFactory(pension_type=p2)

    actual = PensionBalance.objects.related()

    assert len(actual) == 1
    assert str(actual[0].pension_type) == 'P1'
    assert actual[0].pension_type.user.username == 'bob'


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
