from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...auths.factories import UserFactory
from ...savings.factories import (SavingBalanceFactory, SavingFactory,
                                  SavingTypeFactory)
from ...savings.models import SavingBalance
from ..models import Saving, SavingBalance, SavingType


pytestmark = pytest.mark.django_db


@pytest.fixture()
def _savings_extra():
    SavingFactory(
        date=date(1999, 1, 1),
        price=1.0,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=1.0,
        fee=0.25,
        account=AccountFactory(title='Account2'),
        saving_type=SavingTypeFactory(title='Saving1')
    )


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
def test_saving_type_str():
    i = SavingFactory.build()

    assert str(i) == '1999-01-01: Savings'


def test_saving_type_items_user(get_user):
    SavingTypeFactory(title='T1', user=UserFactory())
    SavingTypeFactory(title='T2', user=UserFactory(username='u2'))

    actual = SavingType.objects.items()

    assert actual.count() == 1
    assert actual[0].title == 'T1'


def test_saving_type_day_sum_empty_month(get_user, savings):
    expect = []

    actual = list(Saving.objects.day_saving_type(1999, 2))

    assert expect == actual


def test_saving_type_items_closed_in_past(get_user):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items(3000)

    assert actual.count() == 1


def test_saving_type_items_closed_in_future(get_user):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items(1000)

    assert actual.count() == 2


def test_saving_type_items_closed_in_current_year(get_user):
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items(2000)

    assert actual.count() == 2


def test_saving_type_post_save_new_saving_balance(get_user):
    obj = SavingType(title='s1', user=UserFactory())
    obj.save()

    actual = SavingBalance.objects.items()

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 's1'


def test_saving_type_post_save_new_account_balance(get_user):
    AccountFactory()

    obj = SavingType(title='s1', user=UserFactory())
    obj.save()

    actual = AccountBalance.objects.items()

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'


# ----------------------------------------------------------------------------
#                                                                       Saving
# ----------------------------------------------------------------------------
def test_saving_str():
    actual = SavingTypeFactory.build()

    assert str(actual) == 'Savings'


def test_saving_related(get_user):
    u1 = UserFactory()
    u2 = UserFactory(username='XXX')
    t1 = SavingTypeFactory(title='T1', user=u1)
    t2 = SavingTypeFactory(title='T2', user=u2)

    SavingFactory(saving_type=t1)
    SavingFactory(saving_type=t2)

    actual = Saving.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == 'T1'


def test_saving_items(get_user):
    SavingFactory()

    assert len(Saving.objects.items()) == 1


def test_saving_month_sum(get_user, savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.month_type_sum(1999))

    assert expect == actual


def test_saving_type_day_sum(get_user, savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.day_saving_type(1999, 1))

    assert expect == actual


def test_saving_day_sum(get_user, _savings_extra):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(2.0)},
    ]

    actual = list(Saving.objects.day_saving(1999, 1))

    assert expect == actual


def test_saving_months_sum(get_user, savings):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(5.75)}]

    actual = list(Saving.objects.month_saving(1999))

    assert expect == actual


def test_saving_items_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.items().values()


def test_saving_year_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.year(1999).values()


def test_saving_month_saving_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.month_saving(1999).values()


def test_saving_month_type_sum_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.month_type_sum(1999).values()


def test_saving_day_saving_type_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.day_saving_type(1999, 1).values()


def test_saving_day_saving_query_count(get_user, django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        Saving.objects.day_saving(1999, 1).values()


def test_saving_summary_from(get_user, savings):
    expect = [{
        'title': 'Account1',
        's_past': 1.25,
        's_now': 3.5,
    }, {
        'title': 'Account2',
        's_past': 0.25,
        's_now': 2.25,
    }]

    actual = [*Saving.objects.summary_from(1999).order_by('account__title')]

    assert expect == actual


def test_saving_summary_to(get_user, savings):
    expect = [{
        'title': 'Saving1',
        's_past': 1.25,
        's_now': 3.5,
        's_fee_past': 0.25,
        's_fee_now': 0.5,

    }, {
        'title': 'Saving2',
        's_past': 0.25,
        's_now': 2.25,
        's_fee_past': 0.0,
        's_fee_now': 0.25,
    }]

    actual = [*Saving.objects.summary_to(1999).order_by('saving_type__title')]

    assert expect == actual


@freeze_time('1999-01-01')
def test_saving_year_with_type_closed_in_future(get_user):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=2000)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = Saving.objects.year(1999)

    assert actual.count() == 2


@freeze_time('1999-01-01')
def test_saving_year_with_type_closed_in_current_year(get_user):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1999)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = Saving.objects.year(1999)

    assert actual.count() == 2


@freeze_time('1999-01-01')
def test_saving_year_with_type_closed_in_past(get_user):
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = Saving.objects.year(1999)

    assert actual.count() == 1


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
def test_saving_balance_init():
    actual = SavingBalanceFactory.build()

    assert str(actual.saving_type) == 'Savings'

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
    actual = SavingBalanceFactory.build()

    assert str(actual) == 'Savings'


@pytest.mark.django_db
def test_saving_balance_related_for_user(get_user):
    u = UserFactory(username='XXX')

    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', user=u)

    SavingBalanceFactory(saving_type=s1)
    SavingBalanceFactory(saving_type=s2)

    actual = SavingBalance.objects.related()

    assert len(actual) == 1
    assert str(actual[0].saving_type) == 'S1'
    assert actual[0].saving_type.user.username == 'bob'


@pytest.mark.django_db
def test_saving_balance_items(get_user):
    SavingBalanceFactory(year=1998)
    SavingBalanceFactory(year=1999)
    SavingBalanceFactory(year=2000)

    actual = SavingBalance.objects.items(1999)

    assert len(actual) == 1


def test_saving_balance_queries(get_user, django_assert_num_queries):
    s1 = SavingTypeFactory(title='s1')
    s2 = SavingTypeFactory(title='s2')

    SavingBalanceFactory(saving_type=s1)
    SavingBalanceFactory(saving_type=s2)

    with django_assert_num_queries(1):
        list(SavingBalance.objects.items().values())


def test_saving_balance_new_post_save_account_balace(get_user):
    a1 = AccountFactory()
    a2 = AccountFactory(title='a2')

    s1 = SavingTypeFactory()

    obj = Saving(
        date=date(1999, 1, 1),
        price=Decimal(1),
        fee=Decimal(0.5),
        account=a1,
        saving_type=s1
    )

    obj.save()

    actual = AccountBalance.objects.items(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Account1'
    assert actual['past'] == 0.0
    assert actual['incomes'] == 0.0
    assert actual['expenses'] == 1.0
    assert actual['balance'] == -1.0


def test_saving_balance_new_post_save_saving_balance(get_user,
                                                     savings,
                                                     savings_close,
                                                     savings_change,
                                                     savings_worth):
    account = AccountFactory()
    s1 = SavingType.objects.get(id=1)

    obj = Saving(
        date=date(1999, 1, 1),
        price=Decimal(0.05),
        fee=Decimal(0.0),
        account=account,
        saving_type=s1
    )

    obj.save()

    actual = SavingBalance.objects.items(1999)

    assert actual.count() == 1

    actual = actual[0]

    assert actual['title'] == 'Saving1'

    assert round(actual['past_amount'], 2) == -1.25
    assert round(actual['past_fee'], 2) == 0.4
    assert round(actual['incomes'], 2) == 0.80
    assert round(actual['fees'], 2) == 0.95
    assert round(actual['invested'], 2) == -0.15
    assert round(actual['market_value'], 2) == 0.15
    assert round(actual['profit_incomes_proc'], 2) == -81.25
    assert round(actual['profit_incomes_sum'], 2) == -0.65
    assert round(actual['profit_invested_proc'], 2) == -200.0
    assert round(actual['profit_invested_sum'], 2) == 0.30
