from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
import pytest

from ..lib.day_spending import DaySpending


@pytest.fixture()
def _expenses():
    return \
    [
        {'date': datetime(1999, 1, 1), 'title': 'N', 'sum': Decimal('9.99'), 'exception_sum': Decimal('0.0')},
        {'date': datetime(1999, 1, 1), 'title': 'O1', 'sum': Decimal('1.0'), 'exception_sum': Decimal('0.0')},
        {'date': datetime(1999, 1, 1), 'title': 'O2', 'sum': Decimal('1.25'), 'exception_sum': Decimal('1.0')},

        {'date': datetime(1999, 1, 2), 'title': 'N', 'sum': Decimal('9.99'), 'exception_sum': Decimal('0.0')},
        {'date': datetime(1999, 1, 2), 'title': 'O1', 'sum': Decimal('0.0'), 'exception_sum': Decimal('0.0')},
        {'date': datetime(1999, 1, 2), 'title': 'O2', 'sum': Decimal('1.05'), 'exception_sum': Decimal('0.0')},

        {'date': datetime(1999, 1, 3), 'title': 'N', 'sum': Decimal('9.99'), 'exception_sum': Decimal('0.0')},
        {'date': datetime(1999, 1, 3), 'title': 'O1', 'sum': Decimal('0.0'), 'exception_sum': Decimal('0.0')},
        {'date': datetime(1999, 1, 3), 'title': 'O2', 'sum': Decimal('0.0'), 'exception_sum': Decimal('0.0')},
    ]


@pytest.fixture()
def _necessary():
    return ['N']


@pytest.fixture()
def _types():
    return ['N', 'O1', 'O2']


@pytest.fixture()
def _df_for_average_calculation():
    df = pd.DataFrame([
        {'total': 1.1, 'date': datetime(1999, 1, 1)},
        {'total': 2.1, 'date': datetime(1999, 1, 2)},
        {'total': 3.1, 'date': datetime(1999, 1, 3)},
        {'total': 4.1, 'date': datetime(1999, 1, 31)},
    ])
    df.set_index('date', inplace=True)

    return df


@pytest.mark.freeze_time('1999-01-02')
def test_avg_per_day(_expenses, _necessary, _types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=_expenses,
        necessary=_necessary,
        types=_types,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.avg_per_day

    assert 1.15 == actual


def test_spending_first_day(_expenses, _necessary, _types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=_expenses,
        necessary=_necessary,
        types=_types,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[0]['date'] == datetime(1999, 1, 1)
    assert actual[0]['day'] == -1.0
    assert actual[0]['full'] == -1.0


def test_spending_second_day(_expenses, _necessary, _types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=_expenses,
        necessary=_necessary,
        types=_types,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[1]['date'] == datetime(1999, 1, 2)
    assert actual[1]['day'] == -0.80
    assert round(actual[1]['full'], 2) == -1.80


def test_spending_first_day_necessary_empty(_expenses, _types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=_expenses,
        necessary=[],
        types=_types,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[0]['date'] == datetime(1999, 1, 1)
    assert actual[0]['day'] == -10.99
    assert actual[0]['full'] == -10.99


def test_spending_first_day_necessary_none(_expenses, _types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=_expenses,
        necessary=None,
        types=_types,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[0]['date'] == datetime(1999, 1, 1)
    assert actual[0]['day'] == -10.99
    assert actual[0]['full'] == -10.99


def test_spending_first_day_all_empty(_expenses, _types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=_expenses,
        necessary=None,
        types=_types,
        day_input=0,
        expenses_free=0,
    )

    actual = obj.spending

    assert actual[0]['date'] == datetime(1999, 1, 1)
    assert actual[0]['day'] == -11.24
    assert actual[0]['full'] == -11.24


def test_spending_balance_expenses_empty(_types):
    obj = DaySpending(
        year=1999,
        month=1,
        expenses=[],
        necessary=[],
        types=_types,
        day_input=0,
        expenses_free=0,
    )

    actual = obj.spending

    for x in actual:
        assert x['total'] == 0.0
        assert x['teoretical'] == 0.0
        assert x['real'] == 0.0
        assert x['day'] == 0.0
        assert x['full'] == 0.0


@pytest.mark.freeze_time("1999-01-02")
def test_average_month_two_days(_df_for_average_calculation):
    o = DaySpending(
        year=1999,
        month=1,
        expenses=[],
        necessary=[],
        types=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = _df_for_average_calculation

    actual = o.avg_per_day
    assert 1.6 == round(actual, 2)


@pytest.mark.freeze_time("1999-01-31")
def test_average_month_last_day(_df_for_average_calculation):
    o = DaySpending(
        year=1999,
        month=1,
        expenses=[],
        necessary=[],
        types=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = _df_for_average_calculation
    actual = o.avg_per_day

    assert round(actual, 2) == 0.34


@pytest.mark.freeze_time("1970-01-01")
def test_average_month_other_year(_df_for_average_calculation):
    o = DaySpending(
        year=1999,
        month=1,
        expenses=[],
        necessary=[],
        types=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = _df_for_average_calculation
    actual = o.avg_per_day

    assert round(actual, 2) == 0.34


def test_average_month_empty_dataframe():
    o = DaySpending(
        year=1999,
        month=1,
        expenses=[],
        necessary=[],
        types=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = pd.DataFrame()
    actual = o.avg_per_day

    assert actual == 0.0


def test_average_month_no_dataframe():
    o = DaySpending(
        year=1999,
        month=1,
        expenses=[],
        necessary=[],
        types=[],
        day_input=0,
        expenses_free=0,
    )

    o._spending = None
    actual = o.avg_per_day

    assert actual == 0.0
