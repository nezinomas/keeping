from datetime import date as dt
from decimal import Decimal

import pytest

from ...expenses.factories import ExpenseFactory
from ...incomes.factories import IncomeFactory
from ...savings.factories import SavingFactory
from ...transactions.factories import TransactionFactory

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _incomes():
    return IncomeFactory()


@pytest.fixture()
def _incomes_past():
    return IncomeFactory(date=dt(1970, 1, 1), amount=Decimal(5000))


@pytest.fixture()
def _savings():
    return SavingFactory()


@pytest.fixture()
def _savings_past():
    return SavingFactory(date=dt(1970, 1, 1), amount=Decimal(
        1000), fee=Decimal(150.50))


@pytest.fixture()
def _transactions():
    return TransactionFactory()


@pytest.fixture()
def _transactions_past():
    return TransactionFactory(date=dt(1970, 1, 1), amount=Decimal(500))


@pytest.fixture()
def _expenses():
    return ExpenseFactory()
    return ExpenseFactory(price=15.15)


@pytest.fixture()
def _expenses_past():
    return ExpenseFactory(date=dt(1970, 1, 1))
    return ExpenseFactory(date=dt(1970, 1, 1), price=15.15)
