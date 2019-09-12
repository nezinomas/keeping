from datetime import date, datetime
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from .. import forms
from ..factories import ExpenseNameFactory, ExpenseTypeFactory
from .helper_session import add_session, add_session_to_request

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _expense_type():
    ExpenseTypeFactory.reset_sequence()
    return ExpenseTypeFactory()


@pytest.fixture()
def _expense_name():
    return ExpenseNameFactory()


@pytest.fixture()
def _account():
    return AccountFactory()


def test_expense_form_init(client):
    forms.ExpenseForm(data={}, year=1)


def test_exepense_form_valid_data(_expense_type, _expense_name, _account):
    form = forms.ExpenseForm(
        data={
            'date': '1970-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': 1,
            'expense_name': 1,
            'account': 1,
            'remark': None,
            'exception': None
        },
        year=1970
    )

    assert form.is_valid()

    e = form.save()

    assert e.date == date(1970, 1, 1)
    assert e.price == round(Decimal(1.12), 2)
    assert e.expense_type == _expense_type
    assert e.expense_name == _expense_name
    assert e.account == _account
    assert e.quantity == 1


def test_expenses_form_blank_data():
    form = forms.ExpenseForm(data={}, year=1)

    assert not form.is_valid()

    errors = {
        'date': ['Šis laukas yra privalomas.'],
        'price': ['Šis laukas yra privalomas.'],
        'quantity': ['Šis laukas yra privalomas.'],
        'expense_type': ['Šis laukas yra privalomas.'],
        'expense_name': ['Šis laukas yra privalomas.'],
        'account': ['Šis laukas yra privalomas.'],
    }
    assert form.errors == errors
