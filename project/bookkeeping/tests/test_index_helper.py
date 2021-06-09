import pytest

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


def test_render_lent_no_data(rf):
    obj = IndexHelper(rf, 1999)
    actual = obj.render_lent()

    assert '' == actual
