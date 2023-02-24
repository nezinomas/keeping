import pytz
from datetime import datetime, timezone
import time_machine
import pytest

from ...accounts.factories import AccountFactory
from ...pensions.factories import PensionTypeFactory
from ..factories import SavingTypeFactory
from ..forms import AccountWorthForm, PensionWorthForm, SavingWorthForm

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------------------
#                                                                            Saving Worth
# ---------------------------------------------------------------------------------------
def test_saving_worth_init():
    SavingWorthForm()

def test_saving_worth_init_fields():
    form = SavingWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="saving_type"' in form


def test_saving_worth_current_user_types(second_user):
    SavingTypeFactory(title='T1')  # user bob, current user
    SavingTypeFactory(title='T2', journal=second_user.journal)  # user tom

    form = SavingWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


@time_machine.travel("1999-2-2 03:02:01")
def test_saving_worth_valid_data():
    t = SavingTypeFactory()

    form = SavingWorthForm(data={
        'date': '1999-1-2',
        'price': '1.0',
        'saving_type': t.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.saving_type.title == t.title


def test_saving_blank_data():
    form = SavingWorthForm({})

    assert not form.is_valid()

    assert 'saving_type' in form.errors


def test_saving_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' not in str(form['saving_type'])


def test_saving_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


def test_saving_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingWorthForm()

    assert 'S1' in str(form['saving_type'])
    assert 'S2' in str(form['saving_type'])


@pytest.mark.parametrize(
    'closed, date, valid',
    [
        ('1999', '2000-1-1', False),
        ('1999', '1999-12-31', True),
        ('1999', '1998-12-31', True),
    ]
)
def test_saving_worth_account_closed_date(closed, date, valid):
    a = SavingTypeFactory(closed=closed)

    form = SavingWorthForm(data={
        'date': date,
        'price': '1.0',
        'saving_type': a.pk,
    })

    if valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert 'date' in form.errors
        assert form.errors['date'][0] == 'Sąskaita uždaryta 1999.'


# ---------------------------------------------------------------------------------------
#                                                                           Account Worth
# ---------------------------------------------------------------------------------------
def test_account_worth_init():
    AccountWorthForm()


def test_account_worth_init_fields():
    form = AccountWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="account"' in form


def test_account_worth_current_user_types(second_user):
    AccountFactory(title='T1')  # user bob, current user
    AccountFactory(title='T2', journal=second_user.journal)  # user tom

    form = AccountWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


@time_machine.travel("1999-01-02 03:02:01")
def test_account_worth_valid_data():
    a = AccountFactory()

    form = AccountWorthForm(data={
        'date': '1999-1-2',
        'price': '1.0',
        'account': a.pk,
    })

    assert form.is_valid()

    data = form.save()

    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.account.title == a.title


def test_account_worth_blank_data():
    form = AccountWorthForm(data={})

    assert not form.is_valid()

    assert 'account' in form.errors


@pytest.mark.parametrize(
    'closed, date, valid',
    [
        ('1999', '2000-1-1', False),
        ('1999', '1999-12-31', True),
        ('1999', '1998-12-31', True),
    ]
)
def test_account_worth_account_closed_date(closed, date, valid):
    a = AccountFactory(closed=closed)

    form = AccountWorthForm(data={
        'date': date,
        'price': '1.0',
        'account': a.pk,
    })

    if valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert 'date' in form.errors
        assert form.errors['date'][0] == 'Sąskaita uždaryta 1999.'


# ---------------------------------------------------------------------------------------
#                                                                           Pension Worth
# ---------------------------------------------------------------------------------------
def test_pension_worth_init():
    PensionWorthForm()


def test_pension_worth_init_fields():
    form = PensionWorthForm().as_p()

    assert '<input type="number" name="price"' in form
    assert '<select name="pension_type"' in form


def test_pension_worth_current_user_types(second_user):
    PensionTypeFactory(title='T1')  # user bob, current user
    PensionTypeFactory(title='T2', journal=second_user.journal)  # user tom

    form = PensionWorthForm().as_p()

    assert 'T1' in form
    assert 'T2' not in form


@time_machine.travel("1999-12-12 3:2:1")
def test_pension_worth_valid_data():
    p = PensionTypeFactory()

    form = PensionWorthForm(data={
        'date': '1999-1-2',
        'price': '1.0',
        'pension_type': p.pk,
    })

    assert form.is_valid()

    data = form.save()


    assert data.date == datetime(1999, 1, 2, 3, 2, 1, tzinfo=timezone.utc)
    assert data.price == 1
    assert data.pension_type.title == p.title


def test_pension_worth_blank_data():
    form = PensionWorthForm(data={})

    assert not form.is_valid()

    assert 'pension_type' in form.errors
