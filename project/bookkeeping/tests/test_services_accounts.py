from types import SimpleNamespace

import pytest
from mock import patch

from ..services.accounts import load_service


@pytest.fixture(name="data")
def fixture_data():
    return [
        SimpleNamespace(x=111, past=1, incomes=2, expenses=3, balance=4, have=5, delta=6),
        SimpleNamespace(x=222, past=1, incomes=2, expenses=3, balance=4, have=5, delta=6),
    ]


@patch('project.bookkeeping.services.accounts.get_data')
def test_total_row(mck, data):
    mck.return_value = data

    actual = load_service(1)

    assert actual["total_row"] == {
        "past": 2,
        "incomes": 4,
        "expenses": 6,
        "balance": 8,
        "have": 10,
        "delta": 12,
    }


@patch('project.bookkeeping.services.accounts.get_data')
def test_total_row_no_data(mck):
    mck.return_value = []
    actual = load_service(1)

    assert actual["total_row"] == {
        "past": 0,
        "incomes": 0,
        "expenses": 0,
        "balance": 0,
        "have": 0,
        "delta": 0,
    }
