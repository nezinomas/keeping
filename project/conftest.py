from datetime import date as dt
from datetime import datetime as dtt

import pytest

from .accounts.factories import AccountFactory
from .bookkeeping.factories import AccountWorthFactory, SavingWorthFactory
from .core.factories import UserFactory
from .expenses.factories import ExpenseFactory
from .incomes.factories import IncomeFactory
from .savings.factories import SavingFactory, SavingTypeFactory
from .transactions.factories import (SavingChangeFactory, SavingCloseFactory,
                                     TransactionFactory)


@pytest.fixture(scope='session')
def user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        u = UserFactory()
    yield u
    with django_db_blocker.unblock():
        u.delete()


@pytest.fixture()
def login(client, user):
    client.login(username='bob', password='123')


@pytest.fixture()
def incomes():
    IncomeFactory(
        price=5.25,
        date=dt(1970, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2.25,
        date=dt(1970, 1, 1),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=2.25,
        date=dt(1970, 1, 31),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=3.25,
        date=dt(1999, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2.25,
        date=dt(1999, 1, 1),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=1.25,
        date=dt(1999, 1, 31),
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def expenses():
    ExpenseFactory(
        date=dt(1999, 1, 1),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1999, 1, 1),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1999, 1, 1),
        price=1.25,
        account=AccountFactory(title='Account2')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=1.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=1.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=dt(1970, 1, 1),
        price=2.25,
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def transactions():
    TransactionFactory(
        date=dt(1999, 1, 1),
        price=2.25,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1999, 1, 1),
        price=2.25,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1999, 1, 1),
        price=3.25,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        price=1.25,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=dt(1970, 1, 1),
        price=5.25,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def savings():
    SavingFactory(
        date=dt(1970, 1, 1),
        price=1.25,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=dt(1970, 1, 1),
        price=0.25,
        fee=0.0,
        account=AccountFactory(title='Account2'),
        saving_type=SavingTypeFactory(title='Saving2')
    )
    SavingFactory(
        date=dt(1999, 1, 1),
        price=1.25,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=dt(1999, 1, 1),
        price=2.25,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=dt(1999, 1, 1),
        price=2.25,
        fee=0.25,
        account=AccountFactory(title='Account2'),
        saving_type=SavingTypeFactory(title='Saving2')
    )


@pytest.fixture()
def savings_close():
    SavingCloseFactory(
        date=dt(1999, 1, 1),
        price=0.25,
        fee=0.05,
        to_account=AccountFactory(title='Account1'),
        from_account=SavingTypeFactory(title='Saving1')
    )
    SavingCloseFactory(
        date=dt(1999, 1, 1),
        price=0.0,
        fee=0.0,
        to_account=AccountFactory(title='Account2'),
        from_account=SavingTypeFactory(title='Saving1')
    )
    SavingCloseFactory(
        date=dt(1970, 1, 1),
        price=0.25,
        fee=0.05,
        to_account=AccountFactory(title='Account1'),
        from_account=SavingTypeFactory(title='Saving1')
    )


@pytest.fixture()
def savings_change():
    SavingChangeFactory(
        date=dt(1999, 1, 1),
        price=1.25,
        fee=0.05,
        to_account=SavingTypeFactory(title='Saving2'),
        from_account=SavingTypeFactory(title='Saving1'),
    )
    SavingChangeFactory(
        date=dt(1970, 1, 1),
        price=2.25,
        fee=0.15,
        to_account=SavingTypeFactory(title='Saving2'),
        from_account=SavingTypeFactory(title='Saving1'),
    )


@pytest.fixture()
def accounts_worth():
    AccountWorthFactory(
        date=dt(1999, 1, 1),
        price=3.25,
        account=AccountFactory(title='Account1')
    )
    AccountWorthFactory(
        date=dt(1999, 1, 1),
        price=8.0,
        account=AccountFactory(title='Account2')
    )
    AccountWorthFactory(
        date=dt(1970, 1, 1),
        price=10,
        account=AccountFactory(title='Account1')
    )
    AccountWorthFactory(
        date=dt(1970, 1, 1),
        price=20,
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def savings_worth():
    SavingWorthFactory(
        date=dt(1999, 1, 1),
        price=0.15,
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingWorthFactory(
        date=dt(1999, 1, 1),
        price=6.15,
        saving_type=SavingTypeFactory(title='Saving2')
    )
    SavingWorthFactory(
        date=dt(1970, 1, 1),
        price=10,
        saving_type=SavingTypeFactory(title='Saving1')
    )
