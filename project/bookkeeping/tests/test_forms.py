from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ..factories import SavingTypeFactory
from ..forms import AccountWorthForm, SavingWorthForm


@pytest.mark.django_db
def test_saving_worth_init():
    SavingWorthForm()


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_saving_blank_data():
    form = SavingWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'saving_type' in form.errors


@pytest.mark.django_db
def test_saving_form_type_closed_in_past():
    t = SavingTypeFactory(title='S1')
    t = SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm(data={}, year=3000)

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


@pytest.mark.django_db
def test_saving_form_type_closed_in_future():
    t = SavingTypeFactory(title='S1')
    t = SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm(data={}, year=1000)

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


@pytest.mark.django_db
def test_saving_form_type_closed_in_current_year():
    t = SavingTypeFactory(title='S1')
    t = SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm(data={}, year=2000)

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_account_worth_init():
    AccountWorthForm()


@pytest.mark.django_db
def test_account_worth_valid_data(mock_crequest):
    a = AccountFactory()

    form = AccountWorthForm(data={
        'price': '1.0',
        'account': a.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.price == Decimal(1.0)
    assert data.account.title == a.title


@pytest.mark.django_db
def test_account_worth_blank_data():
    form = AccountWorthForm(data={})

    assert not form.is_valid()

    assert 'price' in form.errors
    assert 'account' in form.errors
