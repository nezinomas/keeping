from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ...savings.factories import SavingTypeFactory
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_init():
    TransactionForm()


def test_transaction_valid_data(get_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title='Account2')

    form = TransactionForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0'
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_transaction_blank_data():
    form = TransactionForm({})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


def test_transaction_price_null(get_user):
    a_from = AccountFactory()
    a_to = AccountFactory(title='Account2')

    form = TransactionForm({
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '0'
    })

    assert not form.is_valid()

    assert 'price' in form.errors


# ----------------------------------------------------------------------------
#                                                                Saving Change
# ----------------------------------------------------------------------------
def test_saving_change_init(get_user):
    SavingChangeForm()


def test_saving_change_valid_data(get_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title='Savings2')

    form = SavingChangeForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0',
        'fee': '0.25'
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.fee == Decimal(0.25)
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_saving_change_blank_data(get_user):
    form = SavingChangeForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


def test_saving_change_price_null(get_user):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title='Savings2')

    form = SavingChangeForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '0'
    })

    assert not form.is_valid()

    assert 'price' in form.errors


def test_saving_change_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' not in str(form['to_account'])


def test_saving_change_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


def test_saving_change_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_init(get_user):
    SavingCloseForm()


def test_saving_close_valid_data(get_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title='Account2')

    form = SavingCloseForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0',
        'fee': '0.25'
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.fee == Decimal(0.25)
    assert data.from_account == a_from
    assert data.to_account == a_to


def test_saving_close_blank_data(get_user):
    form = SavingCloseForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors



def test_saving_close_price_null(get_user):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title='Account2')

    form = SavingCloseForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '0'
    })

    assert not form.is_valid()

    assert 'price' in form.errors


def test_saving_close_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])


def test_saving_close_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])


def test_saving_close_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm({})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])
