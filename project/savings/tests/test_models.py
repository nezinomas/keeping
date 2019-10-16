from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...core.tests.utils import equal_list_of_dictionaries as assert_
from ...savings.factories import SavingFactory, SavingTypeFactory
from ..models import Saving, SavingType

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


def test_saving_only(savings):
    expect = [{
        'title': 'Saving1',
        'past_amount': 1.25,
        'past_fee': 0.25,
        'incomes': 4.75,
        'fees': 0.75,
        'invested': 4.0,
    }, {
        'title': 'Saving2',
        'past_amount': 0.25,
        'past_fee': 0.0,
        'incomes': 2.50,
        'fees': 0.25,
        'invested': 2.25,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_saving_change_only(savings_change):
    expect = [{
        'title': 'Saving1',
        'past_amount': -2.25,
        'past_fee': 0.15,
        'incomes': -3.50,
        'fees': 0.20,
        'invested': -3.70,
    }, {
        'title': 'Saving2',
        'past_amount': 2.25,
        'past_fee': 0.15,
        'incomes': 3.50,
        'fees': 0.20,
        'invested': 3.30,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_saving_cloce_only(savings_close):
    expect = [{
        'title': 'Saving1',
        'past_amount': -0.25,
        'past_fee': 0.0,
        'incomes': -0.5,
        'fees': 0.0,
        'invested': -0.5,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_saving_year_now(savings, savings_close, savings_change):
    expect = [{
        'title': 'Saving1',
        'past_amount': -1.25,
        'past_fee': 0.40,
        'incomes': 0.75,
        'fees': 0.95,
        'invested': -0.20,
    }, {
        'title': 'Saving2',
        'past_amount': 2.50,
        'past_fee': 0.15,
        'incomes': 6.00,
        'fees': 0.45,
        'invested': 5.55,
    }]

    actual = list(SavingType.objects.balance_year(1999))

    assert_(expect, actual)


def test_saving_year_past(savings, savings_close, savings_change):
    expect = [{
        'title': 'Saving1',
        'past_amount': 0.00,
        'past_fee': 0.0,
        'incomes': -1.25,
        'fees': 0.40,
        'invested': -1.65,
    }, {
        'title': 'Saving2',
        'past_amount': 0.00,
        'past_fee': 0.00,
        'incomes': 2.50,
        'fees': 0.15,
        'invested': 2.35,
    }]

    actual = list(SavingType.objects.balance_year(1970))

    assert_(expect, actual)


def test_saving_empty():
    actual = list(SavingType.objects.balance_year(1))

    assert actual == []


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


def test_savings_type_balance_year_query_count(django_assert_max_num_queries):
    with django_assert_max_num_queries(1):
        [*SavingType.objects.balance_year(1999)]


def test_income_str():
    i = SavingFactory.build()

    assert '1999-01-01: Savings' == str(i)


def test_income_type_str():
    i = SavingTypeFactory.build()

    assert 'Savings' == str(i)


def test_summary(savings):
    expect = [{
        'title': 'Account1',
        's_past': 1.25,
        's_now': 3.5,
        's_fee_past': 0.25,
        's_fee_now': 0.5,

    }, {
        'title': 'Account2',
        's_past': 0.25,
        's_now': 2.25,
        's_fee_past': 0.0,
        's_fee_now': 0.25,
    }]

    actual = [*Saving.objects.summary(1999).order_by('account__title')]

    assert expect == actual
