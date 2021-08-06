from datetime import date, datetime

import mock
import pytest
import pytz

from .accounts.factories import AccountFactory
from .bookkeeping.factories import (AccountWorthFactory, PensionWorthFactory,
                                    SavingWorthFactory)
from .debts.factories import (BorrowFactory, BorrowReturnFactory, LentFactory,
                              LentReturnFactory)
from .expenses.factories import ExpenseFactory
from .incomes.factories import IncomeFactory
from .pensions.factories import PensionFactory
from .savings.factories import SavingFactory, SavingTypeFactory
from .transactions.factories import (SavingChangeFactory, SavingCloseFactory,
                                     TransactionFactory)
from .users.factories import UserFactory


@pytest.fixture()
def main_user(request):
    if 'django_db' in request.keywords:
        user = UserFactory()
    else:
        user = UserFactory.build()

    return user


@pytest.fixture()
def second_user(request):
    if 'django_db' in request.keywords:
        user = UserFactory(username='X', email='x@x.xx')
    else:
        user = UserFactory.build(username='X', email='x@x.xx')

    return user


@pytest.fixture()
def fake_request(rf):
    request = rf.get('/fake/')
    request.user = UserFactory.build()

    return request


@pytest.fixture(autouse=True)
def get_user(monkeypatch, request):
    if 'disable_get_user_patch' in request.keywords:
        return

    if 'django_db' in request.keywords:
        user = UserFactory()
    else:
        user = UserFactory.build()

    mock_func = 'project.core.lib.utils.get_user'
    monkeypatch.setattr(mock_func, lambda: user)

    return user


@pytest.fixture()
def client_logged(client):
    client.login(username='bob', password='123')

    return client


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
def pensions():
    PensionFactory(
        price=1.25,
        fee=0,
        date=date(1974, 1, 1),
    )
    PensionFactory(
        price=2.25,
        fee=0.25,
        date=date(1974, 1, 1),
    )
    PensionFactory(
        price=2.25,
        fee=0,
        date=date(1999, 1, 1),
    )
    PensionFactory(
        price=2.25,
        fee=0.5,
        date=date(1999, 1, 1),
    )


@pytest.fixture()
def accounts_worth():
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




@pytest.fixture()
def savings_worth():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1970, 1, 1, tzinfo=pytz.utc)

        SavingWorthFactory(
            price=10,
            saving_type=SavingTypeFactory(title='Saving1')
        )

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



@pytest.fixture()
def pensions_worth():
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1974, 1, 1, tzinfo=pytz.utc)

        PensionWorthFactory(
            price=6,
        )

    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = datetime(1999, 1, 1, tzinfo=pytz.utc)

        PensionWorthFactory(
            price=2.15,
        )


@pytest.fixture
def borrow_fixture():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    BorrowFactory(date=date(1999, 1, 2), price=1, account=a1)
    BorrowFactory(date=date(1999, 2, 3), price=2, account=a1)
    BorrowFactory(date=date(1999, 3, 4), price=3.1, account=a2)

    BorrowFactory(date=date(1974, 1, 2), price=4, account=a1)
    BorrowFactory(date=date(1974, 2, 3), price=5, account=a1)


@pytest.fixture
def borrow_return_fixture():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    BorrowReturnFactory(date=date(1999, 1, 2), price=0.5, account=a1)
    BorrowReturnFactory(date=date(1999, 2, 3), price=1.5, account=a1)
    BorrowReturnFactory(date=date(1999, 3, 4), price=1.6, account=a2)

    BorrowReturnFactory(date=date(1974, 1, 2), price=3.5, account=a1)
    BorrowReturnFactory(date=date(1974, 2, 3), price=4.5, account=a1)


@pytest.fixture
def lent_fixture():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    LentFactory(date=date(1999, 1, 2), price=1, account=a1)
    LentFactory(date=date(1999, 2, 3), price=2, account=a1)
    LentFactory(date=date(1999, 3, 4), price=3.1, account=a2)

    LentFactory(date=date(1974, 1, 2), price=4, account=a1)
    LentFactory(date=date(1974, 2, 3), price=5, account=a1)


@pytest.fixture
def lent_return_fixture():
    a1 = AccountFactory(title='A1')
    a2 = AccountFactory(title='A2')

    LentReturnFactory(date=date(1999, 1, 2), price=0.5, account=a1)
    LentReturnFactory(date=date(1999, 2, 3), price=1.5, account=a1)
    LentReturnFactory(date=date(1999, 3, 4), price=1.6, account=a2)

    LentReturnFactory(date=date(1974, 1, 2), price=3.5, account=a1)
    LentReturnFactory(date=date(1974, 2, 3), price=4.5, account=a1)
