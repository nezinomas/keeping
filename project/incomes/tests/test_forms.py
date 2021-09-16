from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...users.factories import UserFactory
from ..factories import IncomeTypeFactory
from ..forms import IncomeForm, IncomeTypeForm

pytestmark = pytest.mark.django_db

# ----------------------------------------------------------------------------
#                                                                  Income Type
# ----------------------------------------------------------------------------
def test_income_type_init():
    IncomeTypeForm()


def test_income_type_init_fields():
    form = IncomeTypeForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<select name="type"' in form
    assert '<select name="user"' not in form


def test_income_type_valid_data():
    form = IncomeTypeForm(data={
        'title': 'Title',
        'type': 'salary',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.type == 'salary'
    assert data.journal.title == 'bob Journal'
    assert data.journal.users.first().username == 'bob'


def test_income_type_blank_data():
    form = IncomeTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'title' in form.errors
    assert 'type' in form.errors


def test_income_type_title_null():
    form = IncomeTypeForm(data={'title': None})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_income_type_title_too_long():
    form = IncomeTypeForm(data={'title': 'a'*255})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_income_type_title_too_short():
    form = IncomeTypeForm(data={'title': 'aa'})

    assert not form.is_valid()

    assert 'title' in form.errors


def test_income_type_unique_name():
    b = IncomeTypeFactory(title='XXX')

    form = IncomeTypeForm(
        data={
            'title': 'XXX',
        },
    )

    assert not form.is_valid()


# ----------------------------------------------------------------------------
#                                                                       Income
# ----------------------------------------------------------------------------
def test_income_init():
    IncomeForm()


@freeze_time('1000-01-01')
def test_income_year_initial_value():
    UserFactory()

    form = IncomeForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_income_current_user_types(main_user, second_user):
    IncomeTypeFactory(title='T1', journal=main_user.journal)  # user bob, current user
    IncomeTypeFactory(title='T2', journal=second_user.journal)  # user X

    form = IncomeForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_income_current_user_accounts(main_user, second_user):
    AccountFactory(title='A1', journal=main_user.journal)  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = IncomeForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_expense_select_first_account(main_user, second_user):
    a2 = AccountFactory(title='A2', journal=main_user.journal)
    AccountFactory(title='A1', journal=second_user.journal)

    form = IncomeForm().as_p()

    expect = f'<option value="{a2.pk}" selected>{a2}</option>'
    assert expect in form


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


@freeze_time('1999-1-1')
def test_income_insert_only_three_years_to_past():
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(data={
        'date': '1995-01-01',
        'price': '1.0',
        'remark': 'remark',
        'account': a.pk,
        'income_type': t.pk
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai negali būti mažesni nei 1996' in form.errors['date']


@freeze_time('1999-1-1')
def test_income_insert_only_one_year_to_future():
    a = AccountFactory()
    t = IncomeTypeFactory()

    form = IncomeForm(data={
        'date': '2001-01-01',
        'price': '1.0',
        'remark': 'remark',
        'account': a.pk,
        'income_type': t.pk
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai negali būti didesni nei 2000' in form.errors['date']


def test_income_blank_data():
    form = IncomeForm({})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'price' in form.errors
    assert 'account' in form.errors
    assert 'income_type' in form.errors


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
