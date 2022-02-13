from datetime import date

import pytest

from ...debts.factories import DebtFactory
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from ..lib.views_helpers import IndexHelper

pytestmark = pytest.mark.django_db


def test_percentage_from_incomes(rf):
    IncomeFactory(price=10)
    SavingFactory(price=20)

    obj = IndexHelper(rf, 1999)
    actual = obj.render_savings()

    assert actual['percentage_from_incomes'] == 200.0


def test_render_borrow_no_data(rf):
    obj = IndexHelper(rf, 1999)
    actual = obj.render_borrow()

    assert actual is {}


def test_render_borrow(rf):
    DebtFactory()

    obj = IndexHelper(rf, 1999)
    actual = obj.render_borrow()

    assert 'Paskolinta' in actual['title']
    assert 'Gražino' in actual['title']
    assert 100.0 in actual['data']
    assert 25.0 in actual['data']


def test_render_debt_no_data(rf):
    obj = IndexHelper(rf, 1999)
    actual = obj.render_debt()

    assert {} == actual


def test_render_debt(rf):
    DebtFactory()
    obj = IndexHelper(rf, 1999)
    actual = obj.render_debt()

    assert 'Pasiskolinta' in actual['title']
    assert 'Gražinau' in actual['title']
    assert 100.0 in actual['data']
    assert 25.0 in actual['data']


def test_render_year_balance_short(rf):
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(price=100)
    ExpenseFactory(price=25)
    SavingFactory(price=10)

    obj = IndexHelper(rf, 1999).render_year_balance_short()

    assert 'Metų pradžioje' in obj['title']
    assert 'Metų pabaigoje' in obj['title']
    assert 'Metų balansas' in obj['title']

    assert 5.0 in obj['data']  # Metų pradžioje
    assert 70.0 in obj['data']  # Metų pabaigoje
    assert 5.0 in obj['data']  # Metų balansas


def test_render_year_balance_short_highlight_balance(rf):
    IncomeFactory(date=date(1974, 1, 1), price=5)
    IncomeFactory(price=100)
    ExpenseFactory(price=125)

    obj = IndexHelper(rf, 1999).render_year_balance_short()

    assert obj['data'] == [5.0, -20.0, -25.0]
    assert obj['highlight'] == [False, False, True]
