from dataclasses import asdict

import pytest
from mock import MagicMock

from ...services.index import IndexContextBuilder, IndexDataDTO, IndexDataProvider

MODULE_PATH = "project.bookkeeping.services.index"


def test_balance_context():
    obj = IndexContextBuilder(balance=MagicMock())
    actual = obj.balance_context()

    assert "data" in actual
    assert "total_row" in actual
    assert "amount_end" in actual
    assert "avg_row" in actual


def test_balance_short_context():
    obj = IndexContextBuilder(balance=MagicMock())
    actual = obj.balance_short_context()

    assert "title" in actual
    assert "data" in actual
    assert "highlight" in actual


def test_balance_short_context_data():
    obj = IndexContextBuilder(
        balance=MagicMock(amount_start=5, amount_end=70, year=2021)
    )
    actual = obj.balance_short_context()

    assert actual["title"] == ["2021 pradžioje", "2021 pabaigoje", "Balansas"]
    assert actual["data"] == [5, 70, 65]


def test_balance_short_highlighted():
    obj = IndexContextBuilder(balance=MagicMock(amount_start=5, amount_end=-20))
    actual = obj.balance_short_context()

    assert actual["data"] == [5, -20, -25]
    assert actual["highlight"] == [False, False, True]


def test_chart_balance_context():
    obj = IndexContextBuilder(balance=MagicMock())
    actual = obj.chart_balance_context()

    assert "categories" in actual
    assert "incomes" in actual
    assert "incomes_title" in actual
    assert "expenses" in actual
    assert "expenses_title" in actual


def test_averages_context():
    obj = IndexContextBuilder(balance=MagicMock())
    actual = obj.averages_context()

    assert "title" in actual
    assert "data" in actual


def test_borrow_context():
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={"borrow": {"debt": 99, "debt_return": 66}}
    )
    actual = obj.borrow_context()

    assert "title" in actual
    assert "data" in actual

    assert "Pasiskolinta" in actual["title"]
    assert "Grąžinau" in actual["title"]
    assert actual["data"] == [99, 66]


def test_borrow_context_no_data():
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={"borrow": {"debt": None, "debt_return": None}}
    )
    actual = obj.borrow_context()

    assert actual == {}


def test_lend_context_no_data(main_user):
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={"lend": {"debt": None, "debt_return": None}}
    )
    actual = obj.lend_context()

    assert actual == {}


def test_lend_context():
    obj = IndexContextBuilder(
        balance=MagicMock(), debts={"lend": {"debt": 9, "debt_return": 3}}
    )
    actual = obj.lend_context()

    assert "title" in actual
    assert "data" in actual

    assert "Paskolinta" in actual["title"]
    assert "Grąžino" in actual["title"]
    assert actual["data"] == [9, 3]


def test_index_data_dto():
    dto = IndexDataDTO(
        amount_start=1000,
        monthly_data=[{"month": 1, "sum": 500}],
        debts={"lend": {"debt": 100, "debt_return": 50}},
    )

    assert dto.amount_start == 1000
    assert len(dto.monthly_data) == 1
    assert dto.debts["lend"]["debt"] == 100


def test_index_data_provider_get_amount_start(mocker, main_user):
    main_user.year = 2026

    # Mock the database service
    mock_balance_service = mocker.patch(f"{MODULE_PATH}.AccountBalanceModelService")
    mock_year = mock_balance_service.return_value.year.return_value
    mock_year.aggregate.return_value = {"past__sum": 5000}

    provider = IndexDataProvider(main_user)
    actual = provider._get_amount_start()

    assert actual == 5000
    mock_balance_service.return_value.year.assert_called_once_with(2026)


def test_index_data_provider_get_amount_start_returns_zero_if_none(mocker, main_user):
    main_user.year = 2026
    mock_balance_service = mocker.patch(f"{MODULE_PATH}.AccountBalanceModelService")
    mock_year = mock_balance_service.return_value.year.return_value
    mock_year.aggregate.return_value = {"past__sum": None}

    provider = IndexDataProvider(main_user)
    actual = provider._get_amount_start()

    assert actual == 0


def test_index_data_provider_get_debts(mocker, main_user):
    mock_debt_service = mocker.patch(f"{MODULE_PATH}.DebtModelService")

    # Mocking the responses for "lend" and "borrow" calls
    mock_debt_service.return_value.sum_all.side_effect = [
        {"debt": 100, "debt_return": 50},  # First call (lend)
        {"debt": 200, "debt_return": 0},  # Second call (borrow)
    ]

    provider = IndexDataProvider(main_user)
    actual = provider._get_debts()

    assert actual["lend"] == {"debt": 100, "debt_return": 50}
    assert actual["borrow"] == {"debt": 200, "debt_return": 0}


@pytest.fixture
def mock_year_balance(mocker):
    """Creates a mock YearBalance object with pre-filled properties."""
    mock = mocker.Mock()
    mock.balance = [100, 200, 300]
    mock.total_row = 600
    mock.amount_start = 1000
    mock.amount_end = 1600
    mock.average = 200
    mock.year = 2026
    mock.income_data = [50, 50, 50]
    mock.expense_data = [10, 10, 10]
    mock.avg_incomes = 50
    mock.avg_expenses = 10
    return mock


@pytest.fixture
def mock_debts():
    return {
        "borrow": {"debt": 500, "debt_return": 100},
        "lend": {"debt": 300, "debt_return": 300},
        "empty_debt": {"debt": 0, "debt_return": 0},
    }


def test_index_context_builder_balance_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.balance_context()

    assert actual["data"] == [100, 200, 300]
    assert actual["total_row"] == 600
    assert actual["amount_end"] == 1600
    assert actual["avg_row"] == 200


def test_index_context_builder_balance_short_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.balance_short_context()

    assert actual["data"] == [1000, 1600, 600]  # Start, End, Difference
    assert actual["highlight"] == [False, False, True]
    assert len(actual["title"]) == 3


def test_index_context_builder_averages_context(mock_year_balance):
    builder = IndexContextBuilder(balance=mock_year_balance)
    actual = builder.averages_context()

    assert actual["data"] == [50, 10]
    assert len(actual["title"]) == 2


def test_index_context_builder_borrow_context(mock_year_balance, mock_debts):
    builder = IndexContextBuilder(balance=mock_year_balance, debts=mock_debts)
    actual = builder.borrow_context()

    assert actual["data"] == [500, 100]


def test_index_context_builder_lend_context(mock_year_balance, mock_debts):
    builder = IndexContextBuilder(balance=mock_year_balance, debts=mock_debts)
    actual = builder.lend_context()

    assert actual["data"] == [300, 300]


def test_index_context_builder_debt_context_empty(mock_year_balance, mock_debts):
    # If the debt value is 0 or missing, it should return an empty dict
    builder = IndexContextBuilder(balance=mock_year_balance, debts=mock_debts)

    # Using the generic method directly to test the empty case
    actual = builder._generic_debt_context("empty_debt", "Empty", "Empty Return")

    assert actual == {}
