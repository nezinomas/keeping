from django.forms.models import model_to_dict
import re
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


def test_borrow_checkbox_class():
    form = forms.BorrowForm().as_p()

    pattern = re.compile(fr'<input type="checkbox" name="closed" class="(.*?)>')
    res = re.findall(pattern, form)

    assert 'form-check-input' in res[0]


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
    assert len(form.errors) == 4
    assert 'date' in form.errors
    assert 'name' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors


def test_borrow_same_name_for_diff_user():
    factories.BorrowFactory(name='XXX', user=UserFactory(username='tom'))

    form = forms.BorrowForm({
        'date': '1999-01-04',
        'name': 'XXX',
        'account': AccountFactory(),
        'price': '12',
    })

    assert form.is_bound
    assert form.is_valid()


def test_borrow_unique_name():
    obj = factories.BorrowFactory(name='XXX')

    form = forms.BorrowForm(model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


def test_borrow_unique_name_unclose_with_same_name(rf):
    factories.BorrowFactory(name='XXX')

    obj= factories.BorrowFactory(name='XXX', closed=True)
    obj.closed = False

    form = forms.BorrowForm(data=model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                      Borrow Return Form
# ---------------------------------------------------------------------------------------
def test_borrow_return_init():
    forms.BorrowReturnForm()


def test_borrow_return_init_fields():
    form = forms.BorrowReturnForm().as_p()

    assert '<select name="account"' in form
    assert '<select name="borrow"' in form
    assert '<input type="number" name="price"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form
    assert '<input type="text" name="date"' not in form


def test_borrow_return_current_user_accounts():
    u = UserFactory(username='tom')

    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', user=u)  # user tom

    form = forms.BorrowReturnForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_borrow_return_select_first_account():
    u = UserFactory(username='XXX')
    AccountFactory(title='A1', user=u)

    a2 = AccountFactory(title='A2')

    form = forms.BorrowReturnForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form

@freeze_time('1974-1-2')
def test_borrow_return_valid_data():
    a = AccountFactory()
    b = factories.BorrowFactory()

    form = forms.BorrowReturnForm(
        data={
            'borrow': b.pk,
            'price': '1.1',
            'account': a.pk,
            'remark': 'Rm'
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1974, 1, 2)
    assert e.account == a
    assert e.borrow == b
    assert e.price == Decimal('1.1')
    assert e.remark == 'Rm'


def test_borrow_return_blank_data():
    form = forms.BorrowReturnForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert 'borrow' in form.errors
    assert 'account' in form.errors
    assert 'price' in form.errors


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


def test_lent_checkbox_class():
    form = forms.LentForm().as_p()

    pattern = re.compile(fr'<input type="checkbox" name="closed" class="(.*?)>')
    res = re.findall(pattern, form)

    assert 'form-check-input' in res[0]


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
    form = forms.LentForm(data={
        'date': '1974-01-01',
        'name': 'AA',
        'price': '1',
        'account': AccountFactory(),
    })

    assert not form.is_valid()

    assert 'name' in form.errors


def test_lent_name_too_long():
    form = forms.LentForm(data={
        'date': '1974-01-01',
        'name': 'A'*101,
        'price': '1',
        'account': AccountFactory(),
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

    assert len(form.errors) == 4
    assert 'date' in form.errors
    assert 'name' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors


def test_lent_same_name_for_diff_user():
    factories.LentFactory(name='XXX', user=UserFactory(username='tom'))

    form = forms.LentForm({
        'date': '1999-01-04',
        'name': 'XXX',
        'account': AccountFactory(),
        'price': '12',
    })

    assert form.is_bound
    assert form.is_valid()


def test_lent_unique_name():
    obj = factories.LentFactory(name='XXX')

    form = forms.LentForm(model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


def test_lent_unique_name_unclose_with_same_name(rf):
    factories.LentFactory(name='XXX')

    obj = factories.LentFactory(name='XXX', closed=True)
    obj.closed = False

    form = forms.LentForm(data=model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                        Lent Return Form
# ---------------------------------------------------------------------------------------
def test_lent_return_init():
    forms.LentReturnForm()


def test_lent_return_init_fields():
    form = forms.LentReturnForm().as_p()

    assert '<select name="account"' in form
    assert '<select name="lent"' in form
    assert '<input type="number" name="price"' in form
    assert '<textarea name="remark"' in form

    assert '<select name="user"' not in form
    assert '<input type="text" name="date"' not in form


def test_lent_return_current_user_accounts():
    u = UserFactory(username='tom')

    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', user=u)  # user tom

    form = forms.LentReturnForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_lent_return_select_first_account():
    u = UserFactory(username='XXX')
    AccountFactory(title='A1', user=u)

    a2 = AccountFactory(title='A2')

    form = forms.LentReturnForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


@freeze_time('1974-1-2')
def test_lent_return_valid_data():
    a = AccountFactory()
    b = factories.LentFactory()

    form = forms.LentReturnForm(
        data={
            'lent': b.pk,
            'price': '1.1',
            'account': a.pk,
            'remark': 'Rm'
        },
    )

    assert form.is_valid()

    e = form.save()
    assert e.date == date(1974, 1, 2)
    assert e.account == a
    assert e.lent == b
    assert e.price == Decimal('1.1')
    assert e.remark == 'Rm'


def test_lent_return_blank_data():
    form = forms.LentReturnForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 3
    assert 'lent' in form.errors
    assert 'account' in form.errors
    assert 'price' in form.errors
