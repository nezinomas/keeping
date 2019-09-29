from datetime import date, datetime

import mock
import pytest
import pytz

from .accounts.factories import AccountFactory
from .bookkeeping.factories import AccountWorthFactory, SavingWorthFactory
from .core.factories import UserFactory
from .expenses.factories import ExpenseFactory
from .incomes.factories import IncomeFactory
from .savings.factories import SavingFactory, SavingTypeFactory
from .transactions.factories import (SavingChangeFactory, SavingCloseFactory,
                                     TransactionFactory)


@pytest.fixture()
def user():
    UserFactory()


@pytest.fixture()
def login(client, user):
    client.login(username='bob', password='123')


@pytest.fixture()
def incomes():
    IncomeFactory(
        price=5.25,
        date=date(1970, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2.25,
        date=date(1970, 1, 1),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=2.25,
        date=date(1970, 1, 31),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=3.25,
        date=date(1999, 1, 1),
        account=AccountFactory(title='Account1')
    )
    IncomeFactory(
        price=2.25,
        date=date(1999, 1, 1),
        account=AccountFactory(title='Account2')
    )
    IncomeFactory(
        price=1.25,
        date=date(1999, 2, 1),
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def expenses():
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1999, 12, 1),
        price=1.25,
        account=AccountFactory(title='Account2')
    )
    ExpenseFactory(
        date=date(1970, 1, 1),
        price=1.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1970, 1, 1),
        price=1.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1970, 1, 1),
        price=2.25,
        account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def expenses_january():
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=0.25,
        account=AccountFactory(title='Account1'),
        exception=True
    )
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1999, 1, 11),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1999, 1, 11),
        price=0.25,
        account=AccountFactory(title='Account1')
    )
    ExpenseFactory(
        date=date(1970, 1, 1),
        price=2.25,
        account=AccountFactory(title='Account2')
    )

@pytest.fixture()
def transactions():
    TransactionFactory(
        date=date(1999, 1, 1),
        price=2.25,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=date(1999, 1, 1),
        price=2.25,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=date(1999, 1, 1),
        price=3.25,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )
    TransactionFactory(
        date=date(1970, 1, 1),
        price=1.25,
        to_account=AccountFactory(title='Account2'),
        from_account=AccountFactory(title='Account1')
    )
    TransactionFactory(
        date=date(1970, 1, 1),
        price=5.25,
        to_account=AccountFactory(title='Account1'),
        from_account=AccountFactory(title='Account2')
    )


@pytest.fixture()
def savings():
    SavingFactory(
        date=date(1970, 1, 1),
        price=1.25,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=date(1970, 1, 1),
        price=0.25,
        fee=0.0,
        account=AccountFactory(title='Account2'),
        saving_type=SavingTypeFactory(title='Saving2')
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=1.25,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=2.25,
        fee=0.25,
        account=AccountFactory(title='Account1'),
        saving_type=SavingTypeFactory(title='Saving1')
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=2.25,
        fee=0.25,
        account=AccountFactory(title='Account2'),
        saving_type=SavingTypeFactory(title='Saving2')
    )


@pytest.fixture()
def savings_close():
    SavingCloseFactory(
        date=date(1999, 1, 1),
        price=0.25,
        fee=0.05,
        to_account=AccountFactory(title='Account1'),
        from_account=SavingTypeFactory(title='Saving1')
    )
    SavingCloseFactory(
        date=date(1999, 1, 1),
        price=0.0,
        fee=0.0,
        to_account=AccountFactory(title='Account2'),
        from_account=SavingTypeFactory(title='Saving1')
    )
    SavingCloseFactory(
        date=date(1970, 1, 1),
        price=0.25,
        fee=0.05,
        to_account=AccountFactory(title='Account1'),
        from_account=SavingTypeFactory(title='Saving1')
    )


@pytest.fixture()
def savings_change():
    SavingChangeFactory(
        date=date(1999, 1, 1),
        price=1.25,
        fee=0.05,
        to_account=SavingTypeFactory(title='Saving2'),
        from_account=SavingTypeFactory(title='Saving1'),
    )
    SavingChangeFactory(
        date=date(1970, 1, 1),
        price=2.25,
        fee=0.15,
        to_account=SavingTypeFactory(title='Saving2'),
        from_account=SavingTypeFactory(title='Saving1'),
    )


@pytest.fixture()
def accounts_worth():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1999, 1, 1, tzinfo=pytz.utc)

        AccountWorthFactory(
            date=datetime(1999, 1, 1, tzinfo=pytz.utc),
            price=3.25,
            account=AccountFactory(title='Account1')
        )
        AccountWorthFactory(
            date=datetime(1999, 1, 1, tzinfo=pytz.utc),
            price=8.0,
            account=AccountFactory(title='Account2')
        )

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1970, 1, 1, tzinfo=pytz.utc)

        AccountWorthFactory(
            date=datetime(1970, 1, 1, tzinfo=pytz.utc),
            price=10,
            account=AccountFactory(title='Account1')
        )
        AccountWorthFactory(
            date=datetime(1970, 1, 1, tzinfo=pytz.utc),
            price=20,
            account=AccountFactory(title='Account2')
        )


@pytest.fixture()
def savings_worth():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1999, 1, 1, tzinfo=pytz.utc)

        SavingWorthFactory(
            price=0.15,
            saving_type=SavingTypeFactory(title='Saving1')
        )
        SavingWorthFactory(
            price=6.15,
            saving_type=SavingTypeFactory(title='Saving2')
        )

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1970, 1, 1, tzinfo=pytz.utc)

        SavingWorthFactory(
            price=10,
            saving_type=SavingTypeFactory(title='Saving1')
        )
