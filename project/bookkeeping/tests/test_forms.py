from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...pensions.factories import PensionTypeFactory
from ..factories import SavingTypeFactory
from ..forms import AccountWorthForm, PensionWorthForm, SavingWorthForm

pytestmark = pytest.mark.django_db

# ----------------------------------------------------------------------------
#                                                                 Saving Worth
# ----------------------------------------------------------------------------
def test_saving_worth_init(get_user):
    SavingWorthForm()


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
def test_account_worth_init():
    AccountWorthForm()


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


def test_account_worth_blank_data():
    form = AccountWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'account' in form.errors


# ----------------------------------------------------------------------------
#                                                                Pension Worth
# ----------------------------------------------------------------------------
def test_pension_worth_init():
    PensionWorthForm()


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


def test_pension_worth_blank_data():
    form = PensionWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'pension_type' in form.errors
