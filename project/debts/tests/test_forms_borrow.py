import re
from datetime import date
from decimal import Decimal

import pytest
from django.forms.models import model_to_dict
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from .. import factories, forms

pytestmark = pytest.mark.django_db


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


def test_borrow_checkbox_class():
    form = forms.BorrowForm().as_p()

    pattern = re.compile(r'<input type="checkbox" name="closed" class="(.*?)>')
    res = re.findall(pattern, form)

    assert 'form-check-input' in res[0]


@freeze_time('1000-01-01')
def test_borrow_initial_values():
    UserFactory()

    form = forms.BorrowForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_borrow_current_user_accounts(second_user):
    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = forms.BorrowForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_borrow_select_first_account(second_user):
    a2 = AccountFactory(title='A2')
    AccountFactory(title='A1', journal=second_user.journal)

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
            'closed': False,
            'remark': 'Rm'
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1974, 1, 1)
    assert e.price == Decimal('1.1')
    assert e.returned == Decimal('0')
    assert e.account == a
    assert e.remark == 'Rm'
    assert not e.closed


def test_borrow_blank_data():
    form = forms.BorrowForm(data={})

    assert not form.is_valid()
    assert len(form.errors) == 4
    assert 'date' in form.errors
    assert 'name' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors


def test_borrow_same_name_for_diff_journal(second_user):
    factories.BorrowFactory(name='XXX', journal=second_user.journal)

    form = forms.BorrowForm({
        'date': '1999-01-04',
        'name': 'XXX',
        'account': AccountFactory(),
        'price': '12',
    })

    assert form.is_bound
    assert form.is_valid()


def test_borrow_unique_name():
    obj = factories.BorrowFactory(name='X')

    form = forms.BorrowForm(model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


def test_borrow_unique_name_unclose_with_same_name():
    factories.BorrowFactory(name='X')

    obj= factories.BorrowFactory(name='X', closed=True)
    obj.closed = False

    form = forms.BorrowForm(data=model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


def test_borrow_cant_close():
    obj = factories.BorrowFactory(name='Xxx', closed=True)
    form = forms.BorrowForm(data=model_to_dict(obj))

    assert not form.is_valid()
    assert len(form.errors) == 1
    assert 'closed' in form.errors
