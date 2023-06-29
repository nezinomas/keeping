from datetime import date

import pytest
import time_machine

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


@pytest.mark.parametrize(
    'closed',
    [
        ('2000-01-01'), ('2000'), (2000),
    ]
)
def test_saving_type_valid_data(closed):
    form = SavingTypeForm(data={
        'title': 'Title',
        'closed': closed,
        'type': 'funds',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.closed == 2000
    assert data.journal.title == 'bob Journal'
    assert data.journal.users.first().username == 'bob'


def test_saving_type_blank_data():
    form = SavingTypeForm(data={})

    assert not form.is_valid()

    assert len(form.errors) == 2
    assert 'title' in form.errors
    assert 'type' in form.errors


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


def test_saving_type_closed_in_past(main_user):
    main_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


def test_saving_type_closed_in_future(main_user):
    main_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_saving_type_closed_in_current_year(main_user):
    main_user.year = 2000

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


@time_machine.travel('1974-01-01')
def test_saving_year_initial_value():
    UserFactory()

    form = SavingForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_current_user_types(second_user):
    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', journal=second_user.journal)  # user X

    form = SavingForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


def test_saving_current_user_accounts(second_user):
    AccountFactory(title='S1')  # user bob, current user
    AccountFactory(title='S2', journal=second_user.journal)  # user X

    form = SavingForm().as_p()

    assert 'S1' in form
    assert 'S2' not in form


def test_saving_select_first_account(second_user):
    AccountFactory(title='S1', journal=second_user.journal)
    s2 = AccountFactory(title='S2')

    form = SavingForm().as_p()

    expect = f'<option value="{s2.pk}" selected>{s2}</option>'
    assert expect in form


@time_machine.travel('1999-1-1')
def test_saving_valid_data():
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(data={
        'date': '1999-01-01',
        'price': 0.01,
        'fee': 0.01,
        'remark': 'remark',
        'account': a.pk,
        'saving_type': t.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert data.fee == 1
    assert data.remark == 'remark'
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@time_machine.travel('1999-1-1')
def test_saving_valid_data_with_no_fee():
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(data={
        'date': '1999-01-01',
        'price': 0.01,
        'remark': 'remark',
        'account': a.pk,
        'saving_type': t.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == date(1999, 1, 1)
    assert data.price == 1
    assert not data.fee
    assert data.remark == 'remark'
    assert data.account.title == a.title
    assert data.saving_type.title == t.title


@time_machine.travel('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_saving_invalid_date(year):
    a = AccountFactory()
    t = SavingTypeFactory()

    form = SavingForm(data={
        'date': f'{year}-01-01',
        'price': '10',
        'fee': '2',
        'remark': 'remark',
        'account': a.pk,
        'saving_type': t.pk,
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


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
