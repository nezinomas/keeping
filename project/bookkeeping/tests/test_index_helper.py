import pytest

from ...debts.factories import BorrowFactory, LentFactory
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

    assert '' == actual


def test_render_borrow(rf):
    BorrowFactory()
    obj = IndexHelper(rf, 1999)
    actual = obj.render_borrow()

    assert 'Paskolinau' in actual
    assert 'Gražino' in actual
    assert '100,00' in actual
    assert '25,00' in actual


def test_render_lent_no_data(rf):
    obj = IndexHelper(rf, 1999)
    actual = obj.render_lent()

    assert '' == actual


def test_render_lent(rf):
    LentFactory()
    obj = IndexHelper(rf, 1999)
    actual = obj.render_lent()

    assert 'Pasiskolinau' in actual
    assert 'Gražinau' in actual
    assert '100,00' in actual
    assert '25,00' in actual
