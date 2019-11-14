from datetime import date, datetime
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ..factories import ExpenseNameFactory, ExpenseTypeFactory
from ..forms import ExpenseForm, ExpenseNameForm, ExpenseTypeForm
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


# ----------------------------------------------------------------------------
#                                                                      Expense
# ----------------------------------------------------------------------------
def test_expense_form_init():
    ExpenseForm(data={})


def test_exepense_form_valid_data(mock_crequest,
                                  _expense_type, _expense_name,
                                  _account):
    form = ExpenseForm(
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
    form = ExpenseForm(data={})

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


# ----------------------------------------------------------------------------
#                                                                 Expense Type
# ----------------------------------------------------------------------------
def test_expense_type_init():
    ExpenseTypeForm()


def test_expense_type_init_fields():
    form = ExpenseTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="checkbox" name="necessary"' in form
    assert '<select name="user"' not in form


@pytest.mark.django_db
def test_expense_type_valid_data(get_user):
    form = ExpenseTypeForm(data={
        'title': 'Title',
        'necessary': True
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.necessary
    assert data.user.username == 'bob'


@pytest.mark.django_db
def test_expense_type_blank_data():
    form = ExpenseTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_type_title_null():
    form = ExpenseTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_type_title_too_long():
    form = ExpenseTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_type_title_too_short():
    form = ExpenseTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


# ----------------------------------------------------------------------------
#                                                                 Expense Name
# ----------------------------------------------------------------------------
def test_expense_name_init():
    ExpenseNameForm()


@pytest.mark.django_db
def test_expense_name_valid_data():
    p = ExpenseTypeFactory()

    form = ExpenseNameForm(data={
        'title': 'Title',
        'parent': p.pk,
        'valid_for': 1999
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.valid_for == 1999


@pytest.mark.django_db
def test_expense_name_blank_data():
    form = ExpenseNameForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors
    assert 'parent' in form.errors


@pytest.mark.django_db
def test_expense_name_title_null():
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': None, 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_name_title_too_long():
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': 'a'*255, 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_name_title_too_short():
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': 'x', 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors
