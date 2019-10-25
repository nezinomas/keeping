from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...accounts.models import AccountBalance
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...savings.factories import (SavingBalanceFactory, SavingFactory,
                                  SavingTypeFactory)
from ...savings.models import SavingBalance
from ..models import Saving, SavingBalance, SavingType

pytestmark = pytest.mark.django_db


@pytest.fixture()
def savings_extra():
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


def test_saving_month_sum(savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.month_saving_type(1999))

    assert expect == actual


def test_saving_month_sum_januarty(savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.month_saving_type(1999, 1))

    assert expect == actual


def test_saving_month_sum_february(savings):
    expect = []

    actual = list(Saving.objects.month_saving_type(1999, 2))

    assert expect == actual


def test_saving_type_day_sum(savings):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(3.5), 'title': 'Saving1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(2.25), 'title': 'Saving2'},
    ]

    actual = list(Saving.objects.day_saving_type(1999, 1))

    assert expect == actual


def test_saving_day_sum(savings_extra):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(2.0)},
    ]

    actual = list(Saving.objects.day_saving(1999, 1))

    assert expect == actual


def test_saving_type_day_sum_empty_month(savings):
    expect = []

    actual = list(Saving.objects.day_saving_type(1999, 2))

    assert expect == actual


def test_saving_months_sum(savings):
    expect = [{'date': date(1999, 1, 1), 'sum': Decimal(5.75)}]

    actual = list(Saving.objects.month_saving(1999))

    assert expect == actual


def test_model_saving_str():
    actual = SavingTypeFactory.build()

    assert 'Savings' == str(actual)


def test_savings_items():
    SavingFactory()

    assert 1 == len(Saving.objects.items())


def test_savings_items_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Saving.objects.items()]


def test_savings_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Saving.objects.year(1999)]


def test_savings_month_saving_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Saving.objects.month_saving(1999)]


def test_savings_month_saving_type_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Saving.objects.month_saving_type(1999)]


def test_savings_day_saving_type_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Saving.objects.day_saving_type(1999, 1)]


def test_savings_day_saving_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*Saving.objects.day_saving(1999, 1)]


def test_income_str():
    i = SavingFactory.build()

    assert '1999-01-01: Savings' == str(i)


def test_income_type_str():
    i = SavingTypeFactory.build()

    assert 'Savings' == str(i)


def test_summary_from(savings):
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


def test_summary_to(savings):
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


def test_items_closed_in_past():
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items(3000)

    assert 1 == actual.count()


def test_items_closed_in_future():
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items(1000)

    assert 2 == actual.count()


def test_items_closed_in_current_year():
    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    actual = SavingType.objects.items(2000)

    assert 2 == actual.count()


@freeze_time('1999-01-01')
def test_saving_year_with_type_closed_in_future():
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=2000)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = Saving.objects.year(1999)

    assert 2 == actual.count()


@freeze_time('1999-01-01')
def test_saving_year_with_type_closed_in_current_year():
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1999)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = Saving.objects.year(1999)

    assert 2 == actual.count()


@freeze_time('1999-01-01')
def test_saving_year_with_type_closed_in_past():
    s1 = SavingTypeFactory(title='S1')
    s2 = SavingTypeFactory(title='S2', closed=1974)

    SavingFactory(date=date(1999, 1, 1), saving_type=s1)
    SavingFactory(date=date(1999, 1, 1), saving_type=s2)

    actual = Saving.objects.year(1999)

    assert 1 == actual.count()


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
def test_saving_balance_init():
    actual = SavingBalanceFactory.build()

    assert str(actual.saving) == 'Savings'

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
def test_saving_balance_items():
    SavingBalanceFactory(year=1998)
    SavingBalanceFactory(year=1999)
    SavingBalanceFactory(year=2000)

    actual = SavingBalance.objects.items(1999)

    assert len(actual) == 1


def test_saving_balance_queries(django_assert_num_queries):
    s1 = SavingTypeFactory(title='s1')
    s2 = SavingTypeFactory(title='s2')

    SavingBalanceFactory(saving=s1)
    SavingBalanceFactory(saving=s2)

    with django_assert_num_queries(1) as captured:
        q = SavingBalance.objects.items()
        for i in q:
            title = i['title']


# ----------------------------------------------------------------------------
#                                                             post_save signal
# ----------------------------------------------------------------------------
def test_post_save_account_balace_insert(mock_crequest):
    account = AccountFactory()
    saving = SavingTypeFactory()

    obj = Saving(
        date=date(1999, 1, 1),
        price=Decimal(1),
        fee=Decimal(0.5),
        account=account,
        saving_type=saving
    )

    obj.save()

    actual = AccountBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = actual[0]

    assert 'Account1' == actual['title']
    assert 0.0 == actual['past']
    assert 0.0 == actual['incomes']
    assert 1.0 == actual['expenses']
    assert -1.0 == actual['balance']


def test_post_save_saving_balace_insert(mock_crequest):
    account = AccountFactory()
    saving = SavingTypeFactory()

    obj = Saving(
        date=date(1999, 1, 1),
        price=Decimal(1),
        fee=Decimal(0.5),
        account=account,
        saving_type=saving
    )

    obj.save()

    actual = SavingBalance.objects.items(1999)

    assert 1 == actual.count()

    actual = actual[0]

    assert 'Savings' == actual['title']
    assert 0.0 == actual['past_amount']
    assert 0.0 == actual['past_fee']
    assert 1.0 == actual['incomes']
    assert 0.5 == actual['fees']
    assert 0.5 == actual['invested']
