from types import SimpleNamespace

import pytest

from ..services.accounts import AccountService


@pytest.fixture(name="data")
def fixture_data():
    return SimpleNamespace(
        data=[
            SimpleNamespace(x=111, past=1, incomes=2, expenses=3, balance=4, have=5, delta=6),
            SimpleNamespace(x=222, past=1, incomes=2, expenses=3, balance=4, have=5, delta=6),
        ]
    )


def test_total_row(data):
    actual = AccountService(data).total_row()

    assert actual == {
        "past": 2,
        "incomes": 4,
        "expenses": 6,
        "balance": 8,
        "have": 10,
        "delta": 12,
    }


def test_total_row_no_data():
    data = SimpleNamespace(data=[])
    actual = AccountService(data).total_row()

    assert actual == {}
