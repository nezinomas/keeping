from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from .. import factories, forms

pytestmark = pytest.mark.django_db


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


def test_lent_return_current_user_accounts(second_user):
    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = forms.LentReturnForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_lent_return_select_first_account(second_user):
    AccountFactory(title='A1', journal=second_user.journal)

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


def test_lent_return_only_not_closed():
    b1 = factories.LentFactory(closed=True)
    b2 = factories.LentFactory(closed=False)

    form = forms.LentReturnForm().as_p()

    assert b1.name not in form
    assert b2.name in form


def test_lent_return_price_higher():
    a = AccountFactory()
    b = factories.LentFactory()

    form = forms.LentReturnForm(
        data={
            'lent': b.pk,
            'price': '76',
            'account': a.pk,
        },
    )

    assert not form.is_valid()
    assert 'price' in form.errors
