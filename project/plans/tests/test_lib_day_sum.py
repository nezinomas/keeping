from decimal import Decimal

import pandas as pd
import pytest

from ..factories import (ExpensePlanFactory, ExpenseTypeFactory,
                         IncomePlanFactory, SavingPlanFactory)
from ..lib.day_sum import DaySum


def _round(number):
    return round(number, 2)


def incomes():
    data = {
        'income_type': ['a', 'b'],
        'january': [100.01, 200.02],
        'february': [100.01, 200.02],
    }
    return pd.DataFrame(data).set_index('income_type')


def savings():
    data = {
        'income_type': ['a', 'b'],
        'january': [32.33, 32.33],
        'february': [32.33, 32.33],
    }
    return pd.DataFrame(data).set_index('income_type')


def expenses_necessary():
    return ['necessary1', 'necessary2']


def expenses():
    data = {
        'expense_type': ['ordinary1', 'necessary1', 'ordinary2', 'necessary2'],
        'january': [10.01, 20.02, 30.03, 40.04],
        'february': [10.01, 20.02, 30.03, 40.04],
    }
    return pd.DataFrame(data).set_index('expense_type')


@pytest.fixture(autouse=True)
def mock_get_incomes(monkeypatch, request):
    if 'no_auto_fixture' in request.keywords:
        return

    monkeypatch.setattr(
        DaySum,
        '_get_incomes',
        lambda x: incomes()
    )


@pytest.fixture(autouse=True)
def mock_get_savings(monkeypatch, request):
    if 'no_auto_fixture' in request.keywords:
        return

    monkeypatch.setattr(
        DaySum,
        '_get_savings',
        lambda x: savings()
    )


@pytest.fixture(autouse=True)
def mock_get_expenses(monkeypatch, request):
    if 'no_auto_fixture' in request.keywords:
        return

    monkeypatch.setattr(
        DaySum,
        '_get_expenses',
        lambda x: expenses()
    )


@pytest.fixture(autouse=True)
def mock_get_expenses_necessary(monkeypatch, request):
    if 'no_auto_fixture' in request.keywords:
        return

    monkeypatch.setattr(
        DaySum,
        '_get_expenses_necessary',
        lambda x: expenses_necessary()
    )


#
# database fixtures
#
@pytest.mark.django_db
@pytest.fixture()
def _incomes():
    IncomePlanFactory()


@pytest.mark.django_db
@pytest.fixture()
def _expense_type():
    ExpenseTypeFactory.reset_sequence()

    ExpenseTypeFactory(necessary=True)


@pytest.mark.django_db
@pytest.fixture()
def _savings():
    SavingPlanFactory()
    SavingPlanFactory()


@pytest.mark.django_db
@pytest.fixture()
def _expenses():
    ExpenseTypeFactory.reset_sequence()

    ExpensePlanFactory(january=10.01, february=10.01)
    ExpensePlanFactory(january=20.02, february=20.02)


@pytest.mark.django_db
@pytest.fixture()
def _expenses_necessary():
    ExpenseTypeFactory.reset_sequence()

    ExpensePlanFactory(
        january=11.01, february=11.01,
        expense_type=ExpenseTypeFactory(necessary=True)
    )
    ExpensePlanFactory(
        january=21.02, february=21.02,
        expense_type=ExpenseTypeFactory(necessary=True)
    )


#
# test functions
#
def test_expenses_necessary_sum():
    actual = DaySum(1970).expenses_necessary_sum

    assert 60.06 == actual['january']


def test_incomes_sum():
    actual = DaySum(1970).incomes

    assert 300.03 == _round(actual['january'])


def test_savings_sum():
    actual = DaySum(1970).savings

    assert 64.66 == _round(actual['january'])


def test_expenses_free():
    actual = DaySum(1970).expenses_free

    assert 175.31 == _round(actual['january'])


def test_day_sum1():
    actual = DaySum(1970).day_sum

    assert 5.66 == _round(actual['january'])
    assert 6.26 == _round(actual['february'])


# keliemeji metai
def test_day_sum2():
    actual = DaySum(2020).day_sum

    assert 5.66 == _round(actual['january'])
    assert 6.05 == _round(actual['february'])


def test_plans_stats_list():
    actual = DaySum(1970).plans_stats

    assert 3 == len(actual)


def test_plans_stats_expenses_necessary():
    actual = DaySum(1970).plans_stats

    assert 'Būtinos išlaidos' == actual[0].type
    assert 60.06 == actual[0].january
    assert 60.06 == actual[0].february


def test_plans_stats_expenses_free():
    actual = DaySum(1970).plans_stats
    assert 'Lieka kasdienybei' == actual[1].type
    assert 175.31 == _round(actual[1].january)
    assert 175.31 == _round(actual[1].february)


def test_plans_stats_day_sum():
    actual = DaySum(1970).plans_stats
    assert 'Suma dienai' == actual[2].type
    assert 5.66 == _round(actual[2].january)
    assert 6.26 == _round(actual[2].february)


#
# Integration tests with data from database
#

@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_incomes_year_exist(_incomes):
    actual = DaySum(1970).incomes

    assert 111.11 == actual['january']
    assert 222.11 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_savings_year_exist(_savings):
    actual = DaySum(1970).savings

    assert 64.66 == actual['january']
    assert 64.66 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_incomes_year_not_exist(_incomes):
    actual = DaySum(1).incomes

    assert 0.00 == actual['january']
    assert 0.00 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_savings_year_not_exist(_savings):
    actual = DaySum(1).savings

    assert 0.00 == actual['january']
    assert 0.00 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_necessary_no_necessary(_expenses):
    actual = DaySum(1970).expenses_necessary
    assert not actual


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_necessary_sum_no_necessary(_expenses):
    actual = DaySum(1970).expenses_necessary_sum

    assert 0.00 == actual['january']
    assert 0.00 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_free_no_necessary(_incomes, _savings, _expenses):
    actual = DaySum(1970).expenses_free

    assert 46.45 == _round(actual['january'])
    assert 157.45 == _round(actual['february'])


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_necessary(_expenses_necessary):
    actual = DaySum(1970).expenses_necessary

    assert 2 == len(actual)


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_necessary_sum(_incomes, _savings, _expenses_necessary):
    actual = DaySum(1970).expenses_necessary_sum

    assert 32.03 == actual['january']
    assert 32.03 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_free(_incomes, _savings, _expenses_necessary):
    actual = DaySum(1970).expenses_free

    assert 14.42 == _round(actual['january'])
    assert 125.42 == _round(actual['february'])


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_necessary_both(_expenses_necessary, _expenses):
    actual = DaySum(1970).expenses_necessary

    assert 2 == len(actual)


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_necessary_sum_both(_expenses_necessary, _expenses):
    actual = DaySum(1970).expenses_necessary_sum

    assert 32.03 == actual['january']
    assert 32.03 == actual['february']


@pytest.mark.django_db
@pytest.mark.no_auto_fixture
def test_db_expenses_free_both(_incomes, _savings, _expenses_necessary, _expenses):
    actual = DaySum(1970).expenses_free

    assert 14.42 == _round(actual['january'])
    assert 125.42 == _round(actual['february'])
