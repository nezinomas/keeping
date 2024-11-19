from types import SimpleNamespace

import pytest
from mock import patch

from ..services.accounts import load_service


@pytest.fixture(name="data")
def fixture_data():
    return [
        SimpleNamespace(
            x=111, past=1, incomes=2, expenses=3, balance=4, have=5, delta=6
        ),
        SimpleNamespace(
            x=222, past=1, incomes=2, expenses=3, balance=4, have=5, delta=6
        ),
    ]


@patch("project.bookkeeping.services.accounts.get_data")
def test_total_row(mck, data):
    mck.return_value = data

    actual = load_service(1)["total_row"]

    assert actual["past"] == 2
    assert actual["incomes"] == 4
    assert actual["expenses"] == 6
    assert actual["balance"] == 8
    assert actual["have"] == 10
    assert actual["delta"] == 12


@patch("project.bookkeeping.services.accounts.get_data")
def test_total_row_no_data(mck):
    mck.return_value = []
    actual = load_service(1)["total_row"]

    assert actual["past"] == 0
    assert actual["incomes"] == 0
    assert actual["expenses"] == 0
    assert actual["balance"] == 0
    assert actual["have"] == 0
    assert actual["delta"] == 0
