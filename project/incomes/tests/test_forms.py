from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from ..factories import IncomeTypeFactory
from ..forms import IncomeForm, IncomeTypeForm


pytestmark = pytest.mark.django_db

# ----------------------------------------------------------------------------
#                                                                  Income Type
# ----------------------------------------------------------------------------
def test_income_type_init():
    IncomeTypeForm()


def test_income_type_init_fields():
    form = IncomeTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="user"' not in form


def test_income_type_valid_data(get_user):
    form = IncomeTypeForm(data={
        'title': 'Title',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.user.username == 'bob'


def test_income_type_blank_data():
    form = IncomeTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'title' in form.errors


def test_income_type_title_null():
    form = IncomeTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_income_type_title_too_long():
    form = IncomeTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_income_type_title_too_short():
    form = IncomeTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


# ----------------------------------------------------------------------------
#                                                                       Income
# ----------------------------------------------------------------------------
def test_income_init(get_user):
    IncomeForm()


def test_income_current_user_types(get_user):
    u = UserFactory(username='tom')

    IncomeTypeFactory(title='T1')  # user bob, current user
    IncomeTypeFactory(title='T2', user=u)  # user tom

    form = IncomeForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_income_current_user_accounts(get_user):
    u = UserFactory(username='tom')

    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', user=u)  # user tom

    form = IncomeForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_expense_select_first_account(get_user):
    u = UserFactory(username='XXX')
    AccountFactory(title='A1', user=u)

    a2 = AccountFactory(title='A2')

    form = IncomeForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


def test_income_valid_data(get_user):
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(data={
        'date': '2000-01-01',
        'price': '1.0',
        'remark': 'remark',
        'account': a.pk,
        'income_type': t.pk
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.remark == 'remark'
    assert data.account.title == a.title
    assert data.income_type.title == t.title


def test_income_blank_data(get_user):
    form = IncomeForm({})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors
    assert 'income_type' in form.errors


def test_income_price_null(get_user):
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(data={
        'date': '2000-01-01',
        'price': '0',
        'remark': 'remark',
        'account': a.pk,
        'income_type': t.pk
    })

    assert not form.is_valid()
    assert 'price' in form.errors
