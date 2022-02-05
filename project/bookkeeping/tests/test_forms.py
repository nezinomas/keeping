from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...pensions.factories import PensionTypeFactory
from ..factories import SavingTypeFactory
from ..forms import (AccountWorthForm, DateForm, PensionWorthForm,
                     SavingWorthForm)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                               Date Form
# ---------------------------------------------------------------------------------------
def test_date_form_init():
    DateForm()


def test_date_form_fields():
    form =  DateForm().as_p()

    assert '<input type="text" name="date"' in form


@freeze_time('1000-01-01')
def test_date_form_initial_value():
    form = DateForm().as_p()

    assert '<input type="text" name="date" value="1000-01-01"' in form


def test_date_form_valid_data():
    form = DateForm(data={
        'date': '1999-01-01',
    })

    assert form.is_valid()


def test_date_form_invalid_data():
    form = DateForm(data={
        'date': 'xxx',
    })
    print(f'........... {form.errors}')
    assert not form.is_valid()
    assert 0

def test_date_form_valid_with_no_date():
    form = DateForm(data={
        'date': None,
    })

    assert form.is_valid()


# ---------------------------------------------------------------------------------------
#                                                                            Saving Worth
# ---------------------------------------------------------------------------------------
def test_saving_worth_init():
    SavingWorthForm()

def test_saving_worth_init_fields():
    form = SavingWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="saving_type"' in form


def test_saving_worth_current_user_types(second_user):
    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', journal=second_user.journal)  # user tom

    form = SavingWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_saving_worth_valid_data():
    t = SavingTypeFactory()

    form = SavingWorthForm(data={
        'price': '1.0',
        'saving_type': t.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.saving_type.title == t.title


def test_saving_blank_data():
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


# ---------------------------------------------------------------------------------------
#                                                                           Account Worth
# ---------------------------------------------------------------------------------------
def test_account_worth_init():
    AccountWorthForm()


def test_account_worth_init_fields():
    form = AccountWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="account"' in form


def test_account_worth_current_user_types(second_user):
    AccountFactory(title='T1')  # user bob, current user
    AccountFactory(title='T2', journal=second_user.journal)  # user tom

    form = AccountWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_account_worth_valid_data():
    a = AccountFactory()

    form = AccountWorthForm(data={
        'price': '1.0',
        'account': a.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.account.title == a.title


def test_account_worth_blank_data():
    form = AccountWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'account' in form.errors


# ---------------------------------------------------------------------------------------
#                                                                           Pension Worth
# ---------------------------------------------------------------------------------------
def test_pension_worth_init():
    PensionWorthForm()


def test_pension_worth_init_fields():
    form = PensionWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="pension_type"' in form


def test_pension_worth_current_user_types(second_user):
    PensionTypeFactory(title='T1')  # user bob, current user
    PensionTypeFactory(title='T2', journal=second_user.journal)  # user tom

    form = PensionWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_pension_worth_valid_data():
    p = PensionTypeFactory()

    form = PensionWorthForm(data={
        'price': '1.0',
        'pension_type': p.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.pension_type.title == p.title


def test_pension_worth_blank_data():
    form = PensionWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'pension_type' in form.errors
