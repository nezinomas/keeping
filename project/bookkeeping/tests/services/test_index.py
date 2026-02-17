from mock import MagicMock

from ...services.index import IndexService


def test_balance_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.balance_context()

    assert "data" in actual
    assert "total_row" in actual
    assert "amount_end" in actual
    assert "avg_row" in actual


def test_balance_short_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.balance_short_context()

    assert "title" in actual
    assert "data" in actual
    assert "highlight" in actual


def test_balance_short_context_data():
    obj = IndexService(balance=MagicMock(amount_start=5, amount_end=70, year=2021))
    actual = obj.balance_short_context()

    assert actual["title"] == ["2021 pradžioje", "2021 pabaigoje", "Balansas"]
    assert actual["data"] == [5, 70, 65]


def test_balance_short_highlighted():
    obj = IndexService(balance=MagicMock(amount_start=5, amount_end=-20))
    actual = obj.balance_short_context()

    assert actual["data"] == [5, -20, -25]
    assert actual["highlight"] == [False, False, True]


def test_chart_balance_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.chart_balance_context()

    assert "categories" in actual
    assert "incomes" in actual
    assert "incomes_title" in actual
    assert "expenses" in actual
    assert "expenses_title" in actual


def test_averages_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.averages_context()

    assert "title" in actual
    assert "data" in actual


def test_borrow_context():
    obj = IndexService(
        balance=MagicMock(), debts={"borrow": {"debt": 99, "debt_return": 66}}
    )
    actual = obj.borrow_context()

    assert "title" in actual
    assert "data" in actual

    assert "Pasiskolinta" in actual["title"]
    assert "Grąžinau" in actual["title"]
    assert actual["data"] == [99, 66]


def test_borrow_context_no_data():
    obj = IndexService(
        balance=MagicMock(), debts={"borrow": {"debt": None, "debt_return": None}}
    )
    actual = obj.borrow_context()

    assert actual == {}


def test_lend_context_no_data(main_user):
    obj = IndexService(
        balance=MagicMock(), debts={"lend": {"debt": None, "debt_return": None}}
    )
    actual = obj.lend_context()

    assert actual == {}


def test_lend_context():
    obj = IndexService(
        balance=MagicMock(), debts={"lend": {"debt": 9, "debt_return": 3}}
    )
    actual = obj.lend_context()

    assert "title" in actual
    assert "data" in actual

    assert "Paskolinta" in actual["title"]
    assert "Grąžino" in actual["title"]
    assert actual["data"] == [9, 3]
