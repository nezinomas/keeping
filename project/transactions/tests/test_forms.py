from datetime import date
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory
from ...savings.factories import SavingTypeFactory
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm


def test_transactions_init():
    TransactionForm()


@pytest.mark.django_db
def test_transactions_valid_data(mock_crequest):
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


@pytest.mark.django_db
def test_transactions_blank_data():
    form = TransactionForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


@pytest.mark.django_db
def test_transactions_price_null():
    a_from = AccountFactory()
    a_to = AccountFactory(title='Account2')

    form = TransactionForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '0'
    })

    assert not form.is_valid()

    assert 'price' in form.errors


def test_savings_close_init(mock_crequest):
    SavingCloseForm()


@pytest.mark.django_db
def test_savings_close_valid_data(mock_crequest):
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


@pytest.mark.django_db
def test_savings_close_blank_data(mock_crequest):
    form = SavingCloseForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


@pytest.mark.django_db
def test_savings_close_price_null(mock_crequest):
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


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_savings_close_form_type_closed_in_past(mock_):
    mock_.return_value.user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_savings_close_form_type_closed_in_future(mock_):
    mock_.return_value.user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_savings_close_form_type_closed_in_current_year(mock_):
    mock_.return_value.user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])


def test_savings_change_init(mock_crequest):
    SavingChangeForm()


@pytest.mark.django_db
def test_savings_change_valid_data(mock_crequest):
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


@pytest.mark.django_db
def test_savings_change_blank_data(mock_crequest):
    form = SavingChangeForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


@pytest.mark.django_db
def test_savings_change_price_null(mock_crequest):
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

@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_savings_change_form_type_closed_in_past(mock_):
    mock_.return_value.user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' not in str(form['to_account'])


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_savings_change_form_type_closed_in_future(mock_):
    mock_.return_value.user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_savings_change_form_type_closed_in_current_year(mock_):
    mock_.return_value.user.year = 2000

    t = SavingTypeFactory(title='S1')
    t = SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])
