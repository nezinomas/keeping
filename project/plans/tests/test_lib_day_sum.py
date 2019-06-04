from decimal import Decimal

import pandas as pd
import pytest

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


def expenses_necessary():
    return ['necessary1', 'necessary2']


def expenses():
    data = {
        'expense_type': ['ordinary1', 'necessary1', 'ordinary2', 'necessary2'],
        'january': [10.01, 20.02, 30.03, 40.04],
        'february': [10.01, 20.02, 30.03, 40.04],
    }
    return pd.DataFrame(data).set_index('expense_type')


@pytest.fixture()
def mock_get_incomes(monkeypatch, request):
    monkeypatch.setattr(
        DaySum,
        '_get_incomes',
        lambda x: incomes()
    )


@pytest.fixture()
def mock_get_expenses(monkeypatch, request):
    monkeypatch.setattr(
        DaySum,
        '_get_expenses',
        lambda x: expenses()
    )


@pytest.fixture()
def mock_get_expenses_necessary(monkeypatch, request):
    monkeypatch.setattr(
        DaySum,
        '_get_expenses_necessary',
        lambda x: expenses_necessary()
    )


def test_expenses_necessary_sum(
    mock_get_incomes,
    mock_get_expenses,
    mock_get_expenses_necessary
):
    actual = DaySum(1970).expenses_necessary_sum

    assert 60.06 == actual['january']


def test_incomes_sum(
    mock_get_incomes,
    mock_get_expenses,
    mock_get_expenses_necessary
):
    actual = DaySum(1970).incomes

    assert 300.03 == _round(actual['january'])


def test_expenses_free(
    mock_get_incomes,
    mock_get_expenses,
    mock_get_expenses_necessary
):
    actual = DaySum(1970).expenses_free

    assert 239.97 == _round(actual['january'])


def test_day_sum1(
    mock_get_incomes,
    mock_get_expenses,
    mock_get_expenses_necessary
):
    actual = DaySum(1970).day_sum

    assert 7.74 == _round(actual['january'])
    assert 8.57 == _round(actual['february'])


# keliemeji metai
def test_day_sum2(
    mock_get_incomes,
    mock_get_expenses,
    mock_get_expenses_necessary
):
    actual = DaySum(2020).day_sum

    assert 7.74 == _round(actual['january'])
    assert 8.27 == _round(actual['february'])
