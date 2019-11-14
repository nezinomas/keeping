from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...auths.factories import UserFactory
from ..factories import ExpenseNameFactory, ExpenseTypeFactory
from ..forms import ExpenseForm, ExpenseNameForm, ExpenseTypeForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                      Expense
# ----------------------------------------------------------------------------
def test_expense_form_init(get_user):
    ExpenseForm(data={})


def test_expense_current_user_expense_types(get_user):
    u = UserFactory(username='tom')

    ExpenseTypeFactory(title='T1')  # user bob, current user
    ExpenseTypeFactory(title='T2', user=u)  # user tom

    form = ExpenseForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_exepense_form_valid_data(get_user):
    a = AccountFactory()
    t = ExpenseTypeFactory()
    n = ExpenseNameFactory(parent=t)

    form = ExpenseForm(
        data={
            'date': '1999-01-01',
            'price': 1.12,
            'quantity': 1,
            'expense_type': t.pk,
            'expense_name': n.pk,
            'account': a.pk,
            'remark': None,
            'exception': None
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1999, 1, 1)
    assert e.price == round(Decimal(1.12), 2)
    assert e.expense_type == t
    assert e.expense_name == n
    assert e.account == a
    assert e.quantity == 1


def test_expenses_form_blank_data(get_user):
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
def test_expense_name_init(get_user):
    ExpenseNameForm()


def test_expense_name_current_user_expense_types(get_user):
    u = UserFactory(username='tom')

    ExpenseTypeFactory(title='T1') # user bob, current user
    ExpenseTypeFactory(title='T2', user=u) # user tom

    form = ExpenseNameForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


@pytest.mark.django_db
def test_expense_name_valid_data(get_user):
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
def test_expense_name_blank_data(get_user):
    form = ExpenseNameForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors
    assert 'parent' in form.errors


@pytest.mark.django_db
def test_expense_name_title_null(get_user):
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': None, 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_name_title_too_long(get_user):
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': 'a'*255, 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_expense_name_title_too_short(get_user):
    p = ExpenseTypeFactory()
    form = ExpenseNameForm(data={'title': 'x', 'parent': p.pk})

    assert not form.is_valid()

    assert 'title' in form.errors
