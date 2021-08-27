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


def test_lent_current_user_accounts(second_user):
    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = forms.LentForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_lent_select_first_account(second_user):
    AccountFactory(title='A1', journal=second_user.journal)

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
    assert e.returned == Decimal('0')
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


def test_lent_same_name_for_diff_journal(second_user):
    factories.LentFactory(name='XXX', journal=second_user.journal)

    form = forms.LentForm({
        'date': '1999-01-04',
        'name': 'XXX',
        'account': AccountFactory(),
        'price': '12',
    })

    assert form.is_bound
    assert form.is_valid()


def test_lent_unique_name():
    obj = factories.LentFactory(name='X')

    form = forms.LentForm(model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors


def test_lent_unique_name_unclose_with_same_name(rf):
    factories.LentFactory(name='X')

    obj = factories.LentFactory(name='X', closed=True)
    obj.closed = False

    form = forms.LentForm(data=model_to_dict(obj))

    assert form.is_bound
    assert not form.is_valid()
    assert 'name' in form.errors
