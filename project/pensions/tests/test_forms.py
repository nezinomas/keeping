from datetime import date
from decimal import Decimal

import pytest

from ...auths.factories import UserFactory
from ..factories import PensionTypeFactory
from ..forms import PensionForm, PensionTypeForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  PensionType
# ----------------------------------------------------------------------------
def test_pension_type_init():
    PensionTypeForm()


def test_pension_type_init_fields():
    form = PensionTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="user"' not in form


def test_pension_type_valid_data(get_user):
    form = PensionTypeForm(data={
        'title': 'Title',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.user.username == 'bob'


def test_pension_type_blank_data():
    form = PensionTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'title' in form.errors


def test_pension_type_title_null():
    form = PensionTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_pension_type_title_too_long():
    form = PensionTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_pension_type_title_too_short():
    form = PensionTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_init(get_user):
    PensionForm()


def test_saving_current_user_types(get_user):
    u = UserFactory(username='tom')

    PensionTypeFactory(title='T1')  # user bob, current user
    PensionTypeFactory(title='T2', user=u)  # user tom

    form = PensionForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_pension_valid_data(get_user):
    t = PensionTypeFactory()

    form = PensionForm(data={
        'date': '2000-01-01',
        'price': '1.0',
        'remark': 'remark',
        'pension_type': t.pk
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.remark == 'remark'
    assert data.pension_type.title == t.title


def test_pension_blank_data(get_user):
    form = PensionForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'pension_type' in form.errors


def test_pension_price_null(get_user):
    t = PensionTypeFactory()

    form = PensionForm(data={
        'date': '2000-01-01',
        'price': '0',
        'remark': 'remark',
        'pension_type': t.pk
    })

    assert not form.is_valid()
    assert 'price' in form.errors
