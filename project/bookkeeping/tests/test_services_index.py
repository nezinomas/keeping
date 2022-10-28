from mock import MagicMock
from ..services.index import IndexService


def test_percentage_from_incomes():
    actual = IndexService.percentage_from_incomes(10, 1.5)

    assert actual == 15


def test_percentage_from_incomes_saving_none():
    actual = IndexService.percentage_from_incomes(10, None)

    assert not actual


def test_balance_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.balance_context()

    assert 'data' in actual
    assert 'total_row' in actual
    assert 'amount_end' in actual
    assert 'avg_row' in actual


def test_balance_short_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.balance_short_context()

    assert 'title' in actual
    assert 'data' in actual
    assert 'highlight' in actual


def test_balance_short_context_data():
    obj = IndexService(balance=MagicMock(amount_start=5, amount_end=70))
    actual = obj.balance_short_context()

    assert actual['title'] == ['Metų pradžioje', 'Metų pabaigoje', 'Metų balansas']
    assert actual['data'] == [5.0, 70.0, 65.0]


def test_balance_short_highlighted():
    obj = IndexService(balance=MagicMock(amount_start=5, amount_end=-20))
    actual = obj.balance_short_context()

    assert actual['data'] == [5.0, -20.0, -25.0]
    assert actual['highlight'] == [False, False, True]


def test_chart_balance_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.chart_balance_context()

    assert 'categories' in actual
    assert 'incomes' in actual
    assert 'incomes_title' in actual
    assert 'expenses' in actual
    assert 'expenses_title' in actual


def test_averages_context():
    obj = IndexService(balance=MagicMock())
    actual = obj.averages_context()

    assert 'title' in actual
    assert 'data' in actual


def test_borrow_context():
    obj = IndexService(balance=MagicMock(borrow_data=[99], borrow_return_data=[66]))
    actual = obj.borrow_context()

    assert 'title' in actual
    assert 'data' in actual

    assert 'Pasiskolinta' in actual['title']
    assert 'Grąžinau' in actual['title']
    assert actual['data'] == [99.0, 66.0]


def test_borrow_context_no_data():
    obj = IndexService(balance=MagicMock())
    actual = obj.borrow_context()

    assert actual == {}


def test_lend_context_no_data():
    obj = IndexService(balance=MagicMock())
    actual = obj.lend_context()

    assert actual == {}


def test_lend_context():
    obj = IndexService(balance=MagicMock(lend_data=[4, 5], lend_return_data=[1, 2]))
    actual = obj.lend_context()

    assert 'title' in actual
    assert 'data' in actual

    assert 'Paskolinta' in actual['title']
    assert 'Grąžino' in actual['title']
    assert actual['data'] == [9.0, 3.0]
