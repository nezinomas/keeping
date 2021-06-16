from datetime import date
from decimal import Decimal

import pytest

from ...journals.factories import JournalFactory
from ...users.factories import UserFactory
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


def test_pension_type_valid_data():
    form = PensionTypeForm(data={
        'title': 'Title',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.journal.user.username == 'bob'


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


def test_pensiong_type_unique_name():
    b = PensionTypeFactory(title='XXX')

    form = PensionTypeForm(
        data={
            'title': 'XXX',
        },
    )

    assert not form.is_valid()


# ----------------------------------------------------------------------------
#                                                                      Pension
# ----------------------------------------------------------------------------
def test_pension_init():
    PensionForm()


def test_pension_init_fields():
    form = PensionForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="pension_type"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="number" name="fee"' in form
    assert '<textarea name="remark"' in form


def test_saving_current_user_types():
    j = JournalFactory(user=UserFactory(username='X'))

    PensionTypeFactory(title='T1')  # user bob, current user
    PensionTypeFactory(title='T2', journal=j)  # user X

    form = PensionForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_pension_valid_data():
    t = PensionTypeFactory()

    form = PensionForm(data={
        'date': '2000-01-01',
        'price': '1.0',
        'fee': '0.0',
        'remark': 'remark',
        'pension_type': t.pk
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(2000, 1, 1)
    assert data.price == Decimal(1.0)
    assert data.fee == Decimal(0.0)
    assert data.remark == 'remark'
    assert data.pension_type.title == t.title


def test_pension_blank_data():
    form = PensionForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'fee' in form.errors
    assert 'pension_type' in form.errors


def test_pension_price_and_fee_null():
    t = PensionTypeFactory()

    form = PensionForm(data={
        'date': '2000-01-01',
        'price': '0',
        'fee': '0',
        'remark': 'remark',
        'pension_type': t.pk
    })

    assert not form.is_valid()
    assert 'price' in form.errors
    assert 'fee' in form.errors


def test_pension_price_negative():
    t = PensionTypeFactory()

    form = PensionForm(data={
        'date': '2000-01-01',
        'price': '-10',
        'fee': '0',
        'remark': 'remark',
        'pension_type': t.pk
    })

    assert not form.is_valid()
    assert 'price' in form.errors


def test_pension_fee_negative():
    t = PensionTypeFactory()

    form = PensionForm(data={
        'date': '2000-01-01',
        'price': '0',
        'fee': '-10',
        'remark': 'remark',
        'pension_type': t.pk
    })

    assert not form.is_valid()
    assert 'fee' in form.errors
