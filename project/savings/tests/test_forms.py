from datetime import date
from decimal import Decimal

import pytest
from mock import patch

from ...accounts.factories import AccountFactory
from ..factories import SavingTypeFactory
from ..forms import SavingForm, SavingTypeForm


def test_saving_init(mock_crequest):
    SavingForm()


@pytest.mark.django_db
def test_saving_valid_data(mock_crequest):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(data={
        'date': '2000-01-01',
        'price': '1.0',
        'fee': '0.25',
        'remark': 'remark',
        'account': a.pk,
        'saving_type': t.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.fee == Decimal(0.25)
    assert data.remark == 'remark'
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@pytest.mark.django_db
def test_saving_blank_data(mock_crequest):
    form = SavingForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors
    assert 'saving_type' in form.errors


@pytest.mark.django_db
def test_saving_price_null(mock_crequest):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(data={
        'date': '2000-01-01',
        'price': '0',
        'remark': 'remark',
        'account': a.pk,
        'saving_type': t.pk
    })

    assert not form.is_valid()
    assert 'price' in form.errors


def test_saving_type_init():
    SavingTypeForm()


@pytest.mark.django_db
def test_saving_type_valid_data(mock_crequest):
    form = SavingTypeForm(data={
        'title': 'Title',
        'closed': '2000',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.closed == 2000


@pytest.mark.django_db
def test_saving_type_blank_data():
    form = SavingTypeForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_saving_type_title_null():
    form = SavingTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_saving_type_title_too_long():
    form = SavingTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_saving_type_title_too_short():
    form = SavingTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_saving_form_type_closed_in_past(mock_):
    mock_.return_value.user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_saving_form_type_closed_in_future(mock_):
    mock_.return_value.user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


@pytest.mark.django_db
@patch('crequest.middleware.CrequestMiddleware.get_request')
def test_saving_form_type_closed_in_current_year(mock_):
    mock_.return_value.user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])
