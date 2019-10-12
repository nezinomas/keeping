from datetime import date
from decimal import Decimal

import pytest

from ...accounts.factories import AccountFactory
from ..factories import IncomeFactory, IncomeTypeFactory
from ..forms import IncomeForm, IncomeTypeForm


def test_income_init():
    IncomeForm()


@pytest.mark.django_db
def test_income_valid_data():
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(data={
        'date': '2000-01-01',
        'price': '1.0',
        'remark': 'remark',
        'account': a.pk,
        'income_type': t.pk
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.remark == 'remark'
    assert data.account.title == a.title
    assert data.income_type.title == t.title


@pytest.mark.django_db
def test_income_blank_data():
    form = IncomeForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors
    assert 'income_type' in form.errors


@pytest.mark.django_db
def test_income_price_null():
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(data={
        'date': '2000-01-01',
        'price': '0',
        'remark': 'remark',
        'account': a.pk,
        'income_type': t.pk
    })

    assert not form.is_valid()
    assert 'price' in form.errors


def test_income_type_init():
    IncomeTypeForm()


@pytest.mark.django_db
def test_income_type_valid_data():
    form = IncomeTypeForm(data={
        'title': 'Title',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'


@pytest.mark.django_db
def test_income_type_blank_data():
    form = IncomeTypeForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_income_type_title_null():
    form = IncomeTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_income_type_title_too_long():
    form = IncomeTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


@pytest.mark.django_db
def test_income_type_title_too_short():
    form = IncomeTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors
