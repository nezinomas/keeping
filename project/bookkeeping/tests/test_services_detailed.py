from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from ..services.detailed import DetailedService


@pytest.fixture(name="data")
def fixture_data():
    return [
        {'date': date(1999, 1, 1), 'sum': Decimal('4'), 'title': 'Y'},
        {'date': date(1999, 2, 1), 'sum': Decimal('8'), 'title': 'Y'},
        {'date': date(1999, 1, 1), 'sum': Decimal('1'), 'title': 'X'},
        {'date': date(1999, 2, 1), 'sum': Decimal('2'), 'title': 'X'},
    ]


def test_incomes_context_name(data):
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]['name'] == 'Pajamos'


def test_incomes_context_data(data):
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]['items'][0]['title'] == 'X'
    assert actual[0]['items'][0]['data'] == [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3.0]
    assert actual[0]['items'][1]['title'] == 'Y'
    assert actual[0]['items'][1]['data'] == [4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12.0]


def test_incomes_context_data_empty_month():
    data = [
        {'date': date(1999, 1, 1), 'sum': Decimal('4'), 'title': 'X'},
        {'date': date(1999, 12, 1), 'sum': Decimal('8'), 'title': 'X'},
    ]
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]['items'][0]['data'] == [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8.0, 12.0]


def test_incomes_context_total_row(data):
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]['total_row'] == [5.0, 10.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15.0]
