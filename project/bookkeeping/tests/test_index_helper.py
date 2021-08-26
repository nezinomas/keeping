import re
from datetime import date

import pytest

from ...debts.factories import BorrowFactory, LentFactory
from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from ..lib.views_helpers import IndexHelper

pytestmark = pytest.mark.django_db


def test_percentage_from_incomes(rf):
    IncomeFactory(price=10)
    SavingFactory(price=2)

    obj = IndexHelper(rf, 1999)
    actual = obj.render_savings()

    assert 'Nuo pajamų: 20,0%' in actual


def test_render_borrow_no_data(rf):
    obj = IndexHelper(rf, 1999)
    actual = obj.render_borrow()

    assert {} == actual


def test_render_borrow(rf):
    BorrowFactory()

    obj = IndexHelper(rf, 1999)
    actual = obj.render_borrow()

    assert 'Paskolinta' in actual['title']
    assert 'Gražino' in actual['title']
    assert 100.0 in actual['data']
    assert 25.0 in actual['data']


def test_render_lent_no_data(rf):
    obj = IndexHelper(rf, 1999)
    actual = obj.render_lent()

    assert {} == actual


def test_render_lent(rf):
    LentFactory()
    obj = IndexHelper(rf, 1999)
    actual = obj.render_lent()

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
