from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time

from ...accounts.factories import AccountFactory
from ...savings.factories import SavingTypeFactory
from ...savings.models import SavingBalance, SavingType
from ...users.factories import UserFactory
from ..forms import SavingChangeForm, SavingCloseForm, TransactionForm

pytestmark = pytest.mark.django_db


# ----------------------------------------------------------------------------
#                                                                  Transaction
# ----------------------------------------------------------------------------
def test_transaction_init():
    TransactionForm()


def test_transaction_init_fields():
    form = TransactionForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<input type="number" name="price"' in form
    assert '<select name="from_account"' in form
    assert '<select name="to_account"' in form


@freeze_time('1000-01-01')
def test_transaction_year_initial_value():
    UserFactory()

    form = TransactionForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_transaction_current_user_accounts(second_user):
    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = TransactionForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_transaction_current_user_accounts_selected_parent(second_user):
    a1 = AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = TransactionForm({
        'from_account': a1.pk
    }).as_p()

    assert '<option value="1" selected>A1</option>' in form
    assert '<option value="1">A1</option>' not in form


def test_transaction_valid_data():
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


@freeze_time('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_transaction_invalid_date(year):
    a_from = AccountFactory()
    a_to = AccountFactory(title='Account2')

    form = TransactionForm(data={
        'date': f'{year}-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0'
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


def test_transaction_blank_data():
    form = TransactionForm({})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


def test_transaction_price_null():
    a_from = AccountFactory()
    a_to = AccountFactory(title='Account2')

    form = TransactionForm({
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '0'
    })

    assert not form.is_valid()

    assert 'price' in form.errors


# ----------------------------------------------------------------------------
#                                                                Saving Change
# ----------------------------------------------------------------------------
def test_saving_change_init():
    SavingChangeForm()


@freeze_time('1000-01-01')
def test_saving_change_year_initial_value():
    UserFactory()

    form = SavingChangeForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_change_current_user(second_user):
    SavingTypeFactory(title='S1')  # user bob, current user
    SavingTypeFactory(title='S2', journal=second_user.journal)  # user X

    form = SavingChangeForm().as_p()

    assert 'S1' in form
    assert 'S2' not in form


def test_saving_change_current_user_accounts_selected_parent(second_user):
    s1 = SavingTypeFactory(title='S1')  # user bob, current user
    SavingTypeFactory(title='S2', journal=second_user.journal)  # user X

    form = SavingChangeForm({
        'from_account': s1.pk
    }).as_p()

    assert '<option value="1" selected>S1</option>' in form
    assert '<option value="1">S1</option>' not in form


def test_saving_change_valid_data():
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


@freeze_time('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_saving_change_invalid_date(year):
    a_from = SavingTypeFactory()
    a_to = SavingTypeFactory(title='Savings2')

    form = SavingChangeForm(data={
        'date': f'{year}-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0',
        'fee': '0.25'
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


def test_saving_change_blank_data():
    form = SavingChangeForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


def test_saving_change_price_null():
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


def test_saving_change_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' not in str(form['to_account'])


def test_saving_change_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


def test_saving_change_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingChangeForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


# ----------------------------------------------------------------------------
#                                                                 Saving Close
# ----------------------------------------------------------------------------
def test_saving_close_init():
    SavingCloseForm()

def test_saving_close_fields():
    form = SavingCloseForm().as_p()

    assert '<input type="text" name="date"' in form
    assert '<select name="to_account"' in form
    assert '<select name="from_account"' in form
    assert '<input type="number" name="price"' in form
    assert '<input type="number" name="fee"' in form
    assert '<input type="checkbox" name="close"' in form


@freeze_time('1000-01-01')
def test_saving_close_year_initial_value():
    UserFactory()

    form = SavingCloseForm().as_p()

    assert '<input type="text" name="date" value="1999-01-01"' in form


def test_saving_close_current_user_saving_types(second_user):
    SavingTypeFactory(title='S1')  # user bob, current user
    SavingTypeFactory(title='S2', journal=second_user.journal)  # user X

    form = SavingCloseForm().as_p()

    assert 'S1' in form
    assert 'S2' not in form


def test_saving_close_current_user_accounts(second_user):
    AccountFactory(title='A1')  # user bob, current user
    AccountFactory(title='A2', journal=second_user.journal)  # user X

    form = SavingCloseForm().as_p()

    assert 'A1' in form
    assert 'A2' not in form


def test_saving_close_valid_data():
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


@freeze_time('1999-2-2')
@pytest.mark.parametrize(
    'year',
    [1998, 2001]
)
def test_saving_close_in_valid_date(year):
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title='Account2')

    form = SavingCloseForm(data={
        'date': f'{year}-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0',
        'fee': '0.25'
    })

    assert not form.is_valid()
    assert 'date' in form.errors
    assert 'Metai turi būti tarp 1999 ir 2000' in form.errors['date']


def test_saving_close_blank_data():
    form = SavingCloseForm(data={})

    assert not form.is_valid()

    assert 'date' in form.errors
    assert 'from_account' in form.errors
    assert 'to_account' in form.errors
    assert 'price' in form.errors


def test_saving_close_price_null():
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


def test_saving_close_form_type_closed_in_past(get_user):
    get_user.year = 3000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])


def test_saving_close_form_type_closed_in_future(get_user):
    get_user.year = 1000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])


def test_saving_close_form_type_closed_in_current_year(get_user):
    get_user.year = 2000

    SavingTypeFactory(title='S1')
    SavingTypeFactory(title='S2', closed=2000)

    form = SavingCloseForm({})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])


@freeze_time('1999-1-1')
def test_saving_close_save_and_close_saving_account():
    a_from = SavingTypeFactory()
    a_to = AccountFactory(title='Account2')

    form = SavingCloseForm(data={
        'date': '1999-01-01',
        'from_account': a_from.pk,
        'to_account': a_to.pk,
        'price': '1.0',
        'fee': '0.25',
        'close': True,
    })

    assert form.is_valid()

    data = form.save()

    actual = SavingType.objects.get(title=a_from.title)

    assert actual.closed == 1999
    assert SavingBalance.objects.all().count() == 0
