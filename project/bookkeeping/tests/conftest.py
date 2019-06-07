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
        amount=Decimal(1000),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        amount=Decimal(2000),
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _incomes_past():
    IncomeFactory(
        amount=Decimal(5000),
        date=dt(1970, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        date=dt(1970, 11, 1),
        amount=Decimal(2000),
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _savings():
    SavingFactory(
        amount=Decimal(500),
        fee=Decimal(15.50),
        account=AccountFactory(title='Account1')
    )


@pytest.fixture()
def _savings_past():
    SavingFactory(
        date=dt(1970, 1, 1),
        amount=Decimal(1000),
        fee=Decimal(150.50),
        account=AccountFactory(title='Account1')
    )
    SavingFactory(
        date=dt(1970, 1, 1),
        amount=Decimal(100),
        fee=Decimal(15.50),
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _transactions():
    TransactionFactory(
        amount=Decimal(200),
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        amount=Decimal(200),
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        amount=Decimal(300),
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _transactions_past():
    TransactionFactory(
        date=dt(1970, 1, 1),
        amount=Decimal(100),
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        amount=Decimal(100),
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
            date=dt(1970, 11, 1),
            amount=Decimal(500),
            to_account=AccountFactory(title='Account1'),
            from_account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _expenses():
    ExpenseFactory(
        price=Decimal(30.15),
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        price=Decimal(15.15),
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def _expenses_past():
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=Decimal(30.15),
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=Decimal(15.15),
        account=AccountFactory(title='Account2')
    )
