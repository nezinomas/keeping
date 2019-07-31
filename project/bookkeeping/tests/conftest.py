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
def _incomes_from_db():
    IncomeFactory(
        price=5000,
        date=dt(1970, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2000,
        date=dt(1999, 1, 31),
        account=AccountFactory(title='Account2')
    )


def _incomes_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1970, 1, 1)), 5.25, 'Account1'],
            [pd.to_datetime(dt(1970, 1, 1)), 2.25, 'Account2'],
            [pd.to_datetime(dt(1970, 1, 31)), 2.25, 'Account2'],
            [pd.to_datetime(dt(1999, 1, 1)), 3.25, 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 2.25, 'Account2'],
            [pd.to_datetime(dt(1999, 1, 31)), 1.25, 'Account2'],
        ],
        columns=['date', 'price', 'account']
    )
    return df


def _savings_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1970, 1, 1)), 1.25, 0.25, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1970, 1, 1)), 0.25, 0.00, 'Account2', 'Saving2'],
            [pd.to_datetime(dt(1999, 1, 1)), 1.25, 0.25, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1999, 1, 1)), 2.25, 0.25, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1999, 1, 1)), 2.25, 0.25, 'Account2', 'Saving2'],
        ],
        columns=['date', 'price', 'fee', 'account', 'saving_type']
    )
    return df


def _transactions_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1999, 1, 1)), 2.25, 'Account2', 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 2.25, 'Account2', 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 3.25, 'Account1', 'Account2'],
            [pd.to_datetime(dt(1970, 1, 1)), 1.25, 'Account2', 'Account1'],
            [pd.to_datetime(dt(1970, 1, 1)), 5.25, 'Account1', 'Account2'],
        ],
        columns=['date', 'price', 'to_account', 'from_account']
    )
    return df


def _savings_close_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1999, 1, 1)), 0.25, 0.05, 'Account1', 'Saving1'],
            [pd.to_datetime(dt(1970, 1, 1)), 0.25, 0.05, 'Account1', 'Saving1'],
        ],
        columns=['date', 'price', 'fee', 'to_account', 'from_account']
    )
    return df


def _savings_change_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1999, 1, 1)), 1.25, 0.05, 'Saving2', 'Saving1'],
            [pd.to_datetime(dt(1970, 1, 1)), 2.25, 0.15, 'Saving2', 'Saving1'],
        ],
        columns=['date', 'price', 'fee', 'to_account', 'from_account']
    )
    return df


def _expenses_data():
    df = pd.DataFrame(
        [
            [pd.to_datetime(dt(1999, 1, 1)), 0.25, 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 0.25, 'Account1'],
            [pd.to_datetime(dt(1999, 1, 1)), 1.25, 'Account2'],
            [pd.to_datetime(dt(1970, 1, 1)), 1.25, 'Account1'],
            [pd.to_datetime(dt(1970, 1, 1)), 1.25, 'Account1'],
            [pd.to_datetime(dt(1970, 1, 1)), 2.25, 'Account2'],
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
        'savingclose': _savings_close_data(),
    }
    return items


@pytest.fixture
def _incomes():
    items = {
        'account': _accounts_data(),
        'income': _incomes_data(),
    }
    return items


@pytest.fixture
def _expenses():
    items = {
        'account': _accounts_data(),
        'expense': _expenses_data(),
    }
    return items


@pytest.fixture
def _transactions():
    items = {
        'account': _accounts_data(),
        'transaction': _transactions_data(),
    }
    return items


@pytest.fixture
def _savings():
    items = {
        'account': _accounts_data(),
        'saving': _savings_data(),
    }
    return items


@pytest.fixture
def _savings_close():
    items = {
        'account': _accounts_data(),
        'savingclose': _savings_close_data(),
    }
    return items


@pytest.fixture
def _savings_change():
    items = {
        'savingtype': _savings_type_data(),
        'savingchange': _savings_change_data(),
    }
    return items


@pytest.fixture
def _data_savings_close():
    items = {
        'savingtype': _savings_type_data(),
        'savingclose': _savings_close_data(),
    }
    return items


@pytest.fixture
def _data_savings():
    items = {
        'savingtype': _savings_type_data(),
        'saving': _savings_data(),
        'savingchange': _savings_change_data(),
        'savingclose': _savings_close_data(),
    }
    return items
