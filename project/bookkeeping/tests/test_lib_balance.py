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


def test_months_data(data, types):
    actual = balance.create_data(data, types)

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
