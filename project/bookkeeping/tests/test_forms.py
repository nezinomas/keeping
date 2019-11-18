from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...auths.factories import UserFactory
from ...pensions.factories import PensionTypeFactory
from ..factories import SavingTypeFactory
from ..forms import AccountWorthForm, PensionWorthForm, SavingWorthForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                 Saving Worth
# ----------------------------------------------------------------------------
def test_saving_worth_init(get_user):
    SavingWorthForm()

def test_saving_worth_init_fields(get_user):
    form = SavingWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="saving_type"' in form


def test_saving_worth_current_user_types(get_user):
    u = UserFactory(username='tom')

    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', user=u)  # user tom

    form = SavingWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_saving_worth_valid_data(get_user):
    t = SavingTypeFactory()

    form = SavingWorthForm(data={
        'price': '1.0',
        'saving_type': t.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.saving_type.title == t.title


def test_saving_blank_data(get_user):
    form = SavingWorthForm({})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'saving_type' in form.errors


def test_saving_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


def test_saving_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_saving_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


# ----------------------------------------------------------------------------
#                                                                Account Worth
# ----------------------------------------------------------------------------
def test_account_worth_init(get_user):
    AccountWorthForm()


def test_account_worth_init_fields(get_user):
    form = AccountWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="account"' in form


def test_account_worth_current_user_types(get_user):
    u = UserFactory(username='tom')

    AccountFactory(title='T1')  # user bob, current user
    AccountFactory(title='T2', user=u)  # user tom

    form = AccountWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_account_worth_valid_data(get_user):
    a = AccountFactory()

    form = AccountWorthForm(data={
        'price': '1.0',
        'account': a.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.account.title == a.title


def test_account_worth_blank_data(get_user):
    form = AccountWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'account' in form.errors


# ----------------------------------------------------------------------------
#                                                                Pension Worth
# ----------------------------------------------------------------------------
def test_pension_worth_init(get_user):
    PensionWorthForm()


def test_pension_worth_init_fields(get_user):
    form = PensionWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="pension_type"' in form


def test_pension_worth_current_user_types(get_user):
    u = UserFactory(username='tom')

    PensionTypeFactory(title='T1')  # user bob, current user
    PensionTypeFactory(title='T2', user=u)  # user tom

    form = PensionWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_pension_worth_valid_data(get_user):
    p = PensionTypeFactory()

    form = PensionWorthForm(data={
        'price': '1.0',
        'pension_type': p.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.pension_type.title == p.title


def test_pension_worth_blank_data(get_user):
    form = PensionWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'pension_type' in form.errors
