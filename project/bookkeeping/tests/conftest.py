from datetime import date as dt
from decimal import Decimal

import pandas as pd
import pytest

from ...expenses.factories import AccountFactory, ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory, SavingTypeFactory
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
def _savings_type():
    SavingTypeFactory(title='Saving1')
    SavingTypeFactory(title='Saving2')


def _savings_type_data():
    df = pd.DataFrame(
        [
            ['Saving1'],
            ['Saving2'],
        ],
        columns=['title']
    )
    return df


@pytest.fixture()
def _incomes():
    IncomeFactory(
        price=5000,
        date=dt(1970, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2000,
        date=dt(1970, 11, 1),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=3000,
        date=dt(1999, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2000,
        date=dt(1999, 1, 2),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=2000,
        date=dt(1999, 1, 31),
        account=AccountFactory(title='Account2')
    )


def _incomes_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1970, 1, 1)), 5000.00, 'Account1'],
            [pd.to_datetime(dt(1970, 11, 1)), 2000.00, 'Account2'],
            [pd.to_datetime(dt(1999, 1, 1)), 3000.00, 'Account1'],
            [pd.to_datetime(dt(1999, 1, 2)), 2000.00, 'Account2'],
            [pd.to_datetime(dt(1999, 1, 31)), 2000.00, 'Account2'],
        ],
        columns=['date', 'price', 'account']
    )
    return df


@pytest.fixture()
def _savings():
    SavingFactory(
        date=dt(1970, 1, 1),
        price=1000,
        fee=150.50,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )

    SavingFactory(
        date=dt(1999, 1, 1),
        price=500,
        fee=15.50,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )


def _savings_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1970, 1, 1)), 500.0, 75.17, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1970, 1, 31)), 500.0, 70.51, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1970, 1, 31)), 100.0, 15.5, 'Account2', 'Saving2'],
            [pd.to_datetime(dt(1999, 1, 1)), 250.0, 15.25, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1999, 1, 31)), 250.0, 15.25, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1999, 12, 31)), 300.0, 15.5, 'Account2', 'Saving2'],
        ],
        columns=['date', 'price', 'fee', 'account', 'saving_type']
    )
    return df


@pytest.fixture()
def _transactions():
    TransactionFactory(
        date=dt(1999, 1, 1),
        price=200,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1999, 1, 1),
        price=200,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1999, 1, 1),
        price=300,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        price=100,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        price=500,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )


def _transactions_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1999, 1, 1)), 200.00, 'Account2', 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 200.00, 'Account2', 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 300.00, 'Account1', 'Account2'],
            [pd.to_datetime(dt(1970, 1, 1)), 100.00, 'Account2', 'Account1'],
            [pd.to_datetime(dt(1970, 1, 1)), 500.00, 'Account1', 'Account2'],
        ],
        columns=['date', 'price', 'to_account', 'from_account']
    )
    return df


@pytest.fixture()
def _expenses():
    ExpenseFactory(
        date=dt(1999, 1, 1),
        price=30.15,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1999, 1, 31),
        price=30.15,
        account=AccountFactory(title='Account2')
    )
    ExpenseFactory(
        date=dt(1999, 12, 1),
        price=150.98,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1999, 12, 31),
        price=150.98,
        account=AccountFactory(title='Account2')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=130.15,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1970, 1, 31),
        price=130.15,
        account=AccountFactory(title='Account2')
    )
    ExpenseFactory(
        date=dt(1970, 12, 1),
        price=250.17,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1970, 12, 31),
        price=250.17,
        account=AccountFactory(title='Account2')
    )


def _expenses_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1999, 1, 1)), 30.15, 'Account1'],
            [pd.to_datetime(dt(1999, 1, 31)), 30.15, 'Account2'],
            [pd.to_datetime(dt(1999, 12, 1)), 150.98, 'Account1'],
            [pd.to_datetime(dt(1999, 12, 31)), 150.98, 'Account2'],
            [pd.to_datetime(dt(1970, 1, 1)), 130.15, 'Account1'],
            [pd.to_datetime(dt(1970, 1, 31)), 130.15, 'Account2'],
            [pd.to_datetime(dt(1970, 12, 1)), 250.17, 'Account1'],
            [pd.to_datetime(dt(1970, 12, 31)), 250.17, 'Account2'],
        ],
        columns=['date', 'price', 'account']
    )
    return df


@pytest.fixture
def _data():
    items = {
        'account': _accounts_data(),
        'income': _incomes_data(),
        'expense': _expenses_data(),
        'transaction': _transactions_data(),
        'saving': _savings_data(),
        'saving_type': _savings_type_data(),
    }
    return items


@pytest.fixture
def _data_savings():
    items = {
        'saving': _savings_data(),
        'savingtype': _savings_type_data(),
    }
    return items
