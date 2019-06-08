from datetime import date as dt
from decimal import Decimal

import pandas as pd
import pytest

from ...expenses.factories import AccountFactory, ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from ...transactions.factories import TransactionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _accounts():
    AccountFactory(title='Account1')
    AccountFactory(title='Account2')


def _accounts_data():
    df = pd.DataFrame(
        [
            ['Account1'],
            ['Account2'],
        ],
        columns=['title']
    )
    return df


@pytest.fixture()
def _incomes():
    IncomeFactory(
        amount=1000,
        date=dt(1999, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        amount=2000,
        date=dt(1999, 1, 31),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        amount=5000,
        date=dt(1970, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        date=dt(1970, 11, 1),
        amount=2000,
        account=AccountFactory(title='Account2')
    )


def _incomes_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime('1970-01-01'), 5000.00, 'Account1'],
            [pd.to_datetime('1970-11-01'), 2000.00, 'Account2'],
            [pd.to_datetime('1999-01-01'), 1000.00, 'Account1'],
            [pd.to_datetime('1999-01-31'), 2000.00, 'Account1']
        ],
        columns=['date', 'amount', 'account']
    )
    return df


@pytest.fixture()
def _savings():
    SavingFactory(
        amount=500,
        fee=15.50,
        account=AccountFactory(title='Account1')
    )
    SavingFactory(
        date=dt(1970, 1, 1),
        amount=1000,
        fee=150.50,
        account=AccountFactory(title='Account1')
    )
    SavingFactory(
        date=dt(1970, 1, 1),
        amount=100,
        fee=15.50,
        account=AccountFactory(title='Account2')
    )


def _savings_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime('1970-01-01'), 1000.00, 150.50, 'Account1'],
            [pd.to_datetime('1970-01-31'), 100.00, 15.50, 'Account2'],
            [pd.to_datetime('1999-01-01'), 500.00, 15.50, 'Account1'],
            [pd.to_datetime('1999-01-31'), 300.00, 15.50, 'Account2'],
        ],
        columns=['date', 'amount', 'fee', 'account']
    )
    return df


@pytest.fixture()
def _transactions():
    TransactionFactory(
        amount=200,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        amount=200,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        amount=300,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        amount=100,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        amount=100,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1970, 11, 1),
        amount=500,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )


def _transactions_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime('1999-01-01'), 200.00, 'Account2', 'Account1'],
            [pd.to_datetime('1999-01-01'), 200.00, 'Account2', 'Account1'],
            [pd.to_datetime('1999-01-01'), 300.00, 'Account1', 'Account2'],
            [pd.to_datetime('1970-01-01'), 100.00, 'Account2', 'Account1'],
            [pd.to_datetime('1970-01-01'), 500.00, 'Account1', 'Account2'],
        ],
        columns=['date', 'amount', 'to_account', 'from_account']
    )
    return df


@pytest.fixture()
def _expenses():
    ExpenseFactory(
        price=30.15,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        price=15.15,
        account=AccountFactory(title='Account2')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=30.15,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=15.15,
        account=AccountFactory(title='Account2')
    )


def _expenses_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime('1999-01-01'), 30.15, 'Account1'],
            [pd.to_datetime('1999-01-31'), 30.15, 'Account2'],
            [pd.to_datetime('1999-12-01'), 150.15, 'Account1'],
            [pd.to_datetime('1999-12-31'), 150.15, 'Account2'],
            [pd.to_datetime('1970-01-01'), 130.15, 'Account1'],
            [pd.to_datetime('1970-01-31'), 130.15, 'Account2'],
            [pd.to_datetime('1970-12-01'), 250.17, 'Account1'],
            [pd.to_datetime('1970-12-31'), 250.17, 'Account2'],
        ],
        columns=['date', 'price', 'account']
    )
    return df


@pytest.fixture
def _data():
    items = {
        'income': _incomes_data(),
        'expense': _expenses_data(),
        'transaction': _transactions_data(),
        'saving': _savings_data(),
        'account': _accounts_data()
    }
    return items
