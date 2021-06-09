from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from ..factories import SavingTypeFactory
from ..forms import SavingForm, SavingTypeForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Saving Type
# ----------------------------------------------------------------------------
def test_saving_type_init():
    SavingTypeForm()


def test_saving_type_init_fields():
    form = SavingTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="text" name="closed"' in form
    assert '<select name="user"' not in form


def test_saving_type_valid_data():
    form = SavingTypeForm(data={
        'title': 'Title',
        'closed': '2000',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.closed == 2000
    assert data.user.username == 'bob'


def test_saving_type_blank_data():
    form = SavingTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 1
    assert 'title' in form.errors


def test_saving_type_title_null():
    form = SavingTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_saving_type_title_too_long():
    form = SavingTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_saving_type_title_too_short():
    form = SavingTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_saving_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


def test_saving_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_saving_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_saving_type_unique_name():
    b = SavingTypeFactory(title='XXX')

    form = SavingTypeForm(
        data={
            'title': 'XXX',
        },
    )

    assert not form.is_valid()


# ----------------------------------------------------------------------------
#                                                                       Saving
# ----------------------------------------------------------------------------
def test_saving_init():
    SavingForm()


@freeze_time('1000-01-01')
def test_saving_year_initial_value():
    UserFactory()

    form = SavingForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_current_user_types():
    u = UserFactory(username='tom')

    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', user=u)  # user tom

    form = SavingForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_saving_current_user_accounts():
    u = UserFactory(username='tom')

    AccountFactory(title='S1')  # user bob, current user
    AccountFactory(title='S2', user=u)  # user tom

    form = SavingForm().as_p()

    assert 'S1' in form
    assert 'S2' not in form


def test_saving_select_first_account():
    u = UserFactory(username='XXX')
    AccountFactory(title='S1', user=u)

    s2 = AccountFactory(title='S2')

    form = SavingForm().as_p()

    expect = f'<option value="{s2.pk}" selected>{s2}</option>'
    assert expect in form


def test_saving_valid_data():
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


def test_saving_blank_data():
    form = SavingForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors
    assert 'saving_type' in form.errors


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
