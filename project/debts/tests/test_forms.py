from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from .. import factories, forms, models

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                             Borrow Form
# ---------------------------------------------------------------------------------------
def test_borrow_init():
    forms.BorrowForm()


def test_borrow_init_fields():
    form = forms.BorrowForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="account"' in form
    assert '<input type="text" name="name"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="checkbox" name="closed"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form
    assert '<input type="number" name="returned"' not in form


@freeze_time('1000-01-01')
def test_borrow_initial_values():
    UserFactory()

    form = forms.BorrowForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_borrow_current_user_accounts():
    u = UserFactory(username='tom')

    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', user=u)  # user tom

    form = forms.BorrowForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_borrow_select_first_account():
    u = UserFactory(username='XXX')
    AccountFactory(title='A1', user=u)

    a2 = AccountFactory(title='A2')

    form = forms.BorrowForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


def test_borrow_name_too_short():
    a = AccountFactory()
    form = forms.BorrowForm(data={
        'date': '1974-01-01',
        'name': 'AA',
        'price': '1',
        'account': a.pk,
    })

    assert not form.is_valid()

    assert 'name' in form.errors


def test_borrow_name_too_long():
    a = AccountFactory()
    form = forms.BorrowForm(data={
        'date': '1974-01-01',
        'name': 'A'*101,
        'price': '1',
        'account': a.pk,
    })

    assert not form.is_valid()

    assert 'name' in form.errors


def test_borrow_valid_data():
    a = AccountFactory()

    form = forms.BorrowForm(
        data={
            'date': '1974-01-01',
            'name': 'Name',
            'price': '1.1',
            'account': a.pk,
            'closed': True,
            'remark': 'Rm'
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1974, 1, 1)
    assert e.price == Decimal('1.1')
    assert e.account == a
    assert e.remark == 'Rm'
    assert e.closed


def test_borrow_blank_data():
    form = forms.BorrowForm(data={})

    assert not form.is_valid()

    errors = {
        'date': ['Šis laukas yra privalomas.'],
        'name': ['Šis laukas yra privalomas.'],
        'price': ['Šis laukas yra privalomas.'],
        'account': ['Šis laukas yra privalomas.'],
    }
    assert form.errors == errors


# ---------------------------------------------------------------------------------------
#                                                                               Lent Form
# ---------------------------------------------------------------------------------------
def test_lent_init():
    forms.LentForm()


def test_lent_init_fields():
    form = forms.LentForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="account"' in form
    assert '<input type="text" name="name"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="checkbox" name="closed"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form
    assert '<input type="number" name="returned"' not in form


@freeze_time('1000-01-01')
def test_lent_initial_values():
    UserFactory()

    form = forms.LentForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_lent_current_user_accounts():
    u = UserFactory(username='tom')

    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', user=u)  # user tom

    form = forms.LentForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_lent_select_first_account():
    u = UserFactory(username='XXX')
    AccountFactory(title='A1', user=u)

    a2 = AccountFactory(title='A2')

    form = forms.LentForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


def test_lent_name_too_short():
    a = AccountFactory()
    form = forms.LentForm(data={
        'date': '1974-01-01',
        'name': 'AA',
        'price': '1',
        'account': a.pk,
    })

    assert not form.is_valid()

    assert 'name' in form.errors


def test_lent_name_too_long():
    a = AccountFactory()
    form = forms.LentForm(data={
        'date': '1974-01-01',
        'name': 'A'*101,
        'price': '1',
        'account': a.pk,
    })

    assert not form.is_valid()

    assert 'name' in form.errors


def test_lent_valid_data():
    a = AccountFactory()

    form = forms.LentForm(
        data={
            'date': '1974-01-01',
            'name': 'Name',
            'price': '1.1',
            'account': a.pk,
            'closed': True,
            'remark': 'Rm'
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1974, 1, 1)
    assert e.price == Decimal('1.1')
    assert e.account == a
    assert e.remark == 'Rm'
    assert e.closed


def test_lent_blank_data():
    form = forms.LentForm(data={})

    assert not form.is_valid()

    errors = {
        'date': ['Šis laukas yra privalomas.'],
        'name': ['Šis laukas yra privalomas.'],
        'price': ['Šis laukas yra privalomas.'],
        'account': ['Šis laukas yra privalomas.'],
    }
    assert form.errors == errors
