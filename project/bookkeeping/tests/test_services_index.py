from datetime import date

import pytest

from ...debts.factories import BorrowFactory, LendFactory
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from ..services.index import IndexService

pytestmark = pytest.mark.django_db


def test_percentage_from_incomes():
    actual = IndexService.percentage_from_incomes(10, 1.5)

    assert actual == 15


def test_percentage_from_incomes_saving_none():
    actual = IndexService.percentage_from_incomes(10, None)

    assert not actual


def test_balance_context():
    obj = IndexService(1999)
    actual = obj.balance_context()

    assert 'year' in actual
    assert 'data' in actual
    assert 'total_row' in actual
    assert 'amount_end' in actual
    assert 'avg_row' in actual


def test_balance_short_context():
    obj = IndexService(1999)
    actual = obj.balance_short_context()

    assert 'title' in actual
    assert 'data' in actual
    assert 'highlight' in actual


def test_balance_short_context_data():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(price=100)
    ExpenseFactory(price=25)
    SavingFactory(price=10)

    obj = IndexService(1999)
    actual = obj.balance_short_context()

    assert actual['title'] == ['Metų pradžioje', 'Metų pabaigoje', 'Metų balansas']
    assert actual['data'] == [5.0, 70.0, 65.0]


def test_balance_short_highlighted():
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(price=100)
    ExpenseFactory(price=125)

    obj = IndexService(1999)
    actual = obj.balance_short_context()

    assert actual['data'] == [5.0, -20.0, -25.0]
    assert actual['highlight'] == [False, False, True]


def test_chart_balance_context():
    obj = IndexService(1999)
    actual = obj.chart_balance_context()

    assert 'expenses' in actual
    assert 'incomes' in actual


def test_averages_context():
    obj = IndexService(1999)
    actual = obj.averages_context()

    assert 'title' in actual
    assert 'data' in actual


def test_borrow_context():
    BorrowFactory()

    obj = IndexService(1999)
    actual = obj.borrow_context()

    assert 'title' in actual
    assert 'data' in actual

    assert 'Pasiskolinta' in actual['title']
    assert 'Grąžinau' in actual['title']
    assert actual['data'] == [100.0, 0.0]


def test_borrow_context_no_data():
    obj = IndexService(1999)
    actual = obj.borrow_context()

    assert actual == {}


def test_lend_context_no_data():
    obj = IndexService(1999)
    actual = obj.lend_context()

    assert actual == {}


def test_lend_context():
    LendFactory()

    obj = IndexService(1999)
    actual = obj.lend_context()

    assert 'title' in actual
    assert 'data' in actual

    assert 'Paskolinta' in actual['title']
    assert 'Grąžino' in actual['title']
    assert actual['data'] == [100.0, 0.0]
