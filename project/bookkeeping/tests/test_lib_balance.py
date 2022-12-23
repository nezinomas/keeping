from datetime import date
from decimal import Decimal

import pandas as pd
import pytest
from ..lib import balance


@pytest.fixture(name='data')
def fixture_data():
    return ([
        {
            'date': date(1999, 1, 1),
            'title': 'T1',
            'sum': Decimal('1'),
            'exception_sum': Decimal('0.5')
        }, {
            'date': date(1999, 1, 1),
            'title': 'T2',
            'sum': Decimal('2'),
            'exception_sum': Decimal('0')
        }, {
            'date': date(1999, 1, 31),
            'title': 'T1',
            'sum': Decimal('3'),
            'exception_sum': Decimal('0')
        }, {
            'date': date(1999, 12, 1),
            'title': 'T1',
            'sum': Decimal('4'),
            'exception_sum': Decimal('0')
        }, {
            'date': date(1999, 12, 1),
            'title': 'T2',
            'sum': Decimal('5'),
            'exception_sum': Decimal('0')
        },
    ])


@pytest.fixture(name='types')
def fixture_types():
    return ['T1', 'T2', 'T0']


def test_month_data(data, types):
    actual = balance.MakeDataFrame(year=1999, data=data, types=types).expenses

    assert isinstance(actual, pd.DataFrame)

    assert actual.loc['1999-01-01', 'T0'] == 0.0
    assert actual.loc['1999-01-01', 'T1'] == 4.0
    assert actual.loc['1999-01-01', 'T2'] == 2.0

    assert actual.loc['1999-02-01', 'T0'] == 0.0
    assert actual.loc['1999-02-01', 'T1'] == 0.0
    assert actual.loc['1999-02-01', 'T2'] == 0.0

    assert actual.loc['1999-12-01', 'T0'] == 0.0
    assert actual.loc['1999-12-01', 'T1'] == 4.0
    assert actual.loc['1999-12-01', 'T2'] == 5.0


def test_month_exceptions(data, types):
    actual = balance.MakeDataFrame(year=1999, data=data, types=types).exceptions

    assert isinstance(actual, pd.DataFrame)

    assert actual.loc['1999-01-01', 'sum'] == 0.5
    assert actual.loc['1999-02-01', 'sum'] == 0.0
    assert actual.loc['1999-12-01', 'sum'] == 0.0


def test_day_data(data, types):
    actual = balance.MakeDataFrame(year=1999, month=1, data=data, types=types).expenses

    assert isinstance(actual, pd.DataFrame)

    assert actual.loc['1999-01-01', 'T0'] == 0.0
    assert actual.loc['1999-01-01', 'T1'] == 5.0
    assert actual.loc['1999-01-01', 'T2'] == 7.0

    assert actual.loc['1999-01-02', 'T0'] == 0.0
    assert actual.loc['1999-01-02', 'T1'] == 0.0
    assert actual.loc['1999-01-02', 'T2'] == 0.0

    assert actual.loc['1999-01-31', 'T0'] == 0.0
    assert actual.loc['1999-01-31', 'T1'] == 3.0
    assert actual.loc['1999-01-31', 'T2'] == 0.0


def test_day_exceptions(data, types):
    actual = balance.MakeDataFrame(year=1999, month=1, data=data, types=types).exceptions

    assert isinstance(actual, pd.DataFrame)

    assert actual.loc['1999-01-01', 'sum'] == 0.5
    assert actual.loc['1999-01-02', 'sum'] == 0.0
    assert actual.loc['1999-01-31', 'sum'] == 0.0
