import pytest

from ...bookkeeping.forms import AccountWorthForm
from ...expenses.forms import ExpenseForm
from ...incomes.forms import IncomeForm
from ...savings.forms import SavingForm
from ...transactions.forms import SavingCloseForm, TransactionForm
from ..factories import AccountFactory
from ..forms import AccountForm

pytestmark = pytest.mark.django_db

def test_account_init():
    AccountForm()


def test_account_form_has_fields():
    form = AccountForm().as_p()

    assert '<input type="text" name="title"' in form
    assert '<input type="number" name="order"' in form
    assert '<input type="text" name="closed"' in form
    assert '<select name="user"' not in form


def test_account_valid_data():
    form = AccountForm(data={
        'title': 'Title',
        'order': '1',
        'closed': '1999',
    })

    assert form.is_valid()

    data = form.save()

    assert data.title == 'Title'
    assert data.order == 1
    assert data.closed == 1999
    assert data.journal.user.username == 'bob'


def test_account_blank_data():
    form = AccountForm(data={})

    assert not form.is_valid()

    assert 'title' in form.errors
    assert 'order' in form.errors


def test_account_unique_name():
    b = AccountFactory(title='XXX')

    form = AccountForm(
        data={
            'title': 'XXX',
        },
    )

    assert not form.is_valid()


def test_account_closed_in_past_incomes(get_user):
    get_user.year = 3000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = IncomeForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' not in str(form['account'])


def test_account_closed_in_future_incomes(get_user):
    get_user.year = 1000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = IncomeForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_current_year_incomes(get_user):
    get_user.year = 2000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = IncomeForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_past_expenses(get_user):
    get_user.year = 3000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = ExpenseForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' not in str(form['account'])


def test_account_closed_in_future_expenses(get_user):
    get_user.year = 1000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = ExpenseForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_current_year_expenses(get_user):
    get_user.year = 2000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = ExpenseForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_past_transactions(get_user):
    get_user.year = 3000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = TransactionForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' not in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' not in str(form['to_account'])


def test_account_closed_in_future_transactions(get_user):
    get_user.year = 1000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = TransactionForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


def test_account_closed_in_current_year_transactions(get_user):
    get_user.year = 2000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = TransactionForm(data={})

    assert 'S1' in str(form['from_account'])
    assert 'S2' in str(form['from_account'])

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


def test_account_closed_in_past_saving_close(get_user):
    get_user.year = 3000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['to_account'])
    assert 'S2' not in str(form['to_account'])


def test_account_closed_in_future_saving_close(get_user):
    get_user.year = 1000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


def test_account_closed_in_current_year_saving_close(get_user):
    get_user.year = 2000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = SavingCloseForm(data={})

    assert 'S1' in str(form['to_account'])
    assert 'S2' in str(form['to_account'])


def test_account_closed_in_past_saving(get_user):
    get_user.year = 3000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' not in str(form['account'])


def test_account_closed_in_future_saving(get_user):
    get_user.year = 1000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_current_year_saving(get_user):
    get_user.year = 2000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = SavingForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_past_account_worth(get_user):
    get_user.year = 3000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = AccountWorthForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' not in str(form['account'])


def test_account_closed_in_future_account_worth(get_user):
    get_user.year = 1000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = AccountWorthForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])


def test_account_closed_in_current_year_account_worth(get_user):
    get_user.year = 2000

    AccountFactory(title='S1')
    AccountFactory(title='S2', closed=2000)

    form = AccountWorthForm(data={})

    assert 'S1' in str(form['account'])
    assert 'S2' in str(form['account'])
