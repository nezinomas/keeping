from datetime import date as dt
from decimal import Decimal

import pytest

from ...expenses.factories import ExpenseFactory, AccountFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from ...transactions.factories import TransactionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _accounts():
    AccountFactory(title='Account1')
    AccountFactory(title='Account2')


@pytest.fixture()
def _incomes():
    IncomeFactory(
        amount=1000,
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        amount=2000,
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _incomes_past():
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


@pytest.fixture()
def _savings():
    SavingFactory(
        amount=500,
        fee=15.50,
        account=AccountFactory(title='Account1')
    )


@pytest.fixture()
def _savings_past():
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


@pytest.fixture()
def _transactions_past():
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


@pytest.fixture()
def _expenses_past():
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
