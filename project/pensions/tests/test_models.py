from datetime import date, datetime
from decimal import Decimal

import pytest

from ...bookkeeping.factories import PensionWorthFactory
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


def test_pension_type_new_post_save(get_user, pensions):
    obj = PensionType(title='p1')
    obj.save()

    actual = PensionBalance.objects.items()

    assert 2 == actual.count()


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_str():
    p = PensionFactory.build()

    assert str(p) == '1999-01-01: PensionType'


def test_pension_items(pensions):
    assert len(Pension.objects.items()) == 4


def test_pension_items_query_count(django_assert_max_num_queries, pensions):
    with django_assert_max_num_queries(1):
        list(Pension.objects.items().values())


def test_pension_year(pensions):
    assert len(Pension.objects.year(1999)) == 2


def test_pension_year_query_count(django_assert_max_num_queries, pensions):
    with django_assert_max_num_queries(1):
        list(Pension.objects.year(1999).values())


def test_pension_summary_query_count(django_assert_max_num_queries, pensions):
    with django_assert_max_num_queries(1):
        list(Pension.objects.summary(1999).values())


def test_pension_summary(pensions):
    expect = [{
        'id': 1,
        'title': 'PensionType',
        's_past': Decimal(3.5),
        's_now': Decimal(4.5),

    }]

    actual = list(Pension.objects.summary(1999))

    assert expect == actual


def test_pension_new_post_save(get_user):
    PensionWorthFactory()
    pension_type = PensionTypeFactory()

    income = Pension(
        date=date(1999, 1, 1),
        price=Decimal(1),
        pension_type=pension_type
    )

    income.save()

    actual = PensionBalance.objects.items(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'PensionType'

    assert round(actual['past_amount'], 2) == 0.0
    assert round(actual['past_fee'], 2) == 0.0
    assert round(actual['incomes'], 2) == 1.0
    assert round(actual['fees'], 2) == 0.0
    assert round(actual['invested'], 2) == 1.0
    assert round(actual['market_value'], 2) == 0.5
    assert round(actual['profit_incomes_proc'], 2) == -50.0
    assert round(actual['profit_incomes_sum'], 2) == -0.5
    assert round(actual['profit_invested_proc'], 2) == -50.0
    assert round(actual['profit_invested_sum'], 2) == -0.5


def test_pension_new_post_save_count_queries(get_user,
                                             django_assert_max_num_queries):
    PensionBalanceFactory()
    PensionWorthFactory()
    pension_type = PensionTypeFactory()

    income = Pension(
        date=date(1999, 1, 1),
        price=Decimal(1),
        pension_type=pension_type
    )
    with django_assert_max_num_queries(8):
        income.save()


def test_pension_update_post_save_count_queries(get_user,
                                                django_assert_max_num_queries):
    PensionBalanceFactory()
    PensionWorthFactory()
    pension_type = PensionTypeFactory()

    income = Pension(
        date=date(1999, 1, 1),
        price=Decimal(1),
        pension_type=pension_type
    )
    with django_assert_max_num_queries(8):
        income.save()


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
def test_saving_balance_init():
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


def test_saving_balance_str():
    actual = PensionBalanceFactory.build()

    assert str(actual) == 'PensionType'


@pytest.mark.django_db
def test_saving_balance_items():
    PensionBalanceFactory(year=1998)
    PensionBalanceFactory(year=1999)
    PensionBalanceFactory(year=2000)

    actual = PensionBalance.objects.items(1999)

    assert len(actual) == 1


def test_saving_balance_queries(django_assert_num_queries):
    p1 = PensionTypeFactory(title='p1')
    p2 = PensionTypeFactory(title='p2')

    PensionBalanceFactory(pension_type=p1)
    PensionBalanceFactory(pension_type=p2)

    with django_assert_num_queries(1):
        list(PensionBalance.objects.items().values())
