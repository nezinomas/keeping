from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ..factories import SavingFactory, SavingTypeFactory
from ..forms import SavingForm, SavingTypeForm


def test_saving_init():
    SavingForm()


@pytest.mark.django_db
def test_saving_valid_data():
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(data={
        'date': '2000-01-01',
        'price': '1.0',
        'fee': '0.25',
        'remark': 'remark',
        'account': a.pk,
        'saving_type': t.pk
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
def test_saving_blank_data():
    form = SavingForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors
    assert 'saving_type' in form.errors


@pytest.mark.django_db
def test_saving_price_null():
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
def test_saving_type_valid_data():
    form = SavingTypeForm(data={
        'title': 'Title',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'


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
