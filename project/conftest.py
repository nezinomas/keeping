from datetime import date, datetime

import pytest
import pytz

from .accounts.factories import AccountFactory
from .bookkeeping.factories import (
    AccountWorthFactory,
    PensionWorthFactory,
    SavingWorthFactory,
)
from .debts.factories import LendFactory, LendReturnFactory
from .expenses.factories import ExpenseFactory
from .incomes.factories import IncomeFactory
from .pensions.factories import PensionFactory
from .savings.factories import SavingFactory, SavingTypeFactory
from .transactions.factories import (
    SavingChangeFactory,
    SavingCloseFactory,
    TransactionFactory,
)
from .users.factories import UserFactory


@pytest.fixture(autouse=True)
def main_user(monkeypatch, request):
    if "disable_get_user_patch" in request.keywords:
        return None

    if "django_db" in request.keywords:
        user = UserFactory()

        jr = user.journal
        jr.first_record = date(1999, 1, 1)
        jr.save()
    else:
        user = UserFactory.build()

    mock_func = "project.core.lib.utils.get_user"
    monkeypatch.setattr(mock_func, lambda: user)

    return user


@pytest.fixture()
def second_user(request):
    if "django_db" in request.keywords:
        user = UserFactory(username="X", email="x@x.xx")

        jr = user.journal
        jr.first_record = date(1999, 1, 1)
        jr.save()
    else:
        user = UserFactory.build(username="X", email="x@x.xx")

    return user


@pytest.fixture()
def fake_request(rf):
    request = rf.get("/fake/")
    request.user = UserFactory.build()

    return request


@pytest.fixture()
def client_logged(client):
    client.login(username="bob", password="123")

    return client


@pytest.fixture()
def incomes():
    IncomeFactory(
        price=525, date=date(1970, 1, 1), account=AccountFactory(title="Account1")
    )
    IncomeFactory(
        price=225, date=date(1970, 1, 1), account=AccountFactory(title="Account2")
    )
    IncomeFactory(
        price=225, date=date(1970, 1, 31), account=AccountFactory(title="Account2")
    )
    IncomeFactory(
        price=325, date=date(1999, 1, 1), account=AccountFactory(title="Account1")
    )
    IncomeFactory(
        price=225, date=date(1999, 1, 1), account=AccountFactory(title="Account2")
    )
    IncomeFactory(
        price=125, date=date(1999, 2, 1), account=AccountFactory(title="Account2")
    )


@pytest.fixture()
def expenses():
    ExpenseFactory(
        date=date(1999, 1, 1), price=25, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1999, 1, 1), price=25, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1999, 12, 1), price=125, account=AccountFactory(title="Account2")
    )
    ExpenseFactory(
        date=date(1970, 1, 1), price=125, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1970, 1, 1), price=125, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1970, 1, 1), price=225, account=AccountFactory(title="Account2")
    )


@pytest.fixture()
def expenses_january():
    ExpenseFactory(
        date=date(1999, 1, 1),
        price=25,
        account=AccountFactory(title="Account1"),
        exception=True,
    )
    ExpenseFactory(
        date=date(1999, 1, 1), price=25, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1999, 1, 11), price=25, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1999, 1, 11), price=25, account=AccountFactory(title="Account1")
    )
    ExpenseFactory(
        date=date(1970, 1, 1), price=225, account=AccountFactory(title="Account2")
    )


@pytest.fixture()
def transactions():
    TransactionFactory(
        date=date(1999, 1, 1),
        price=225,
        from_account=AccountFactory(title="Account1"),
        to_account=AccountFactory(title="Account2"),
    )
    TransactionFactory(
        date=date(1999, 1, 1),
        price=225,
        from_account=AccountFactory(title="Account1"),
        to_account=AccountFactory(title="Account2"),
    )
    TransactionFactory(
        date=date(1999, 1, 1),
        price=325,
        from_account=AccountFactory(title="Account2"),
        to_account=AccountFactory(title="Account1"),
    )
    TransactionFactory(
        date=date(1970, 1, 1),
        price=125,
        from_account=AccountFactory(title="Account1"),
        to_account=AccountFactory(title="Account2"),
    )
    TransactionFactory(
        date=date(1970, 1, 1),
        price=525,
        from_account=AccountFactory(title="Account2"),
        to_account=AccountFactory(title="Account1"),
    )


@pytest.fixture()
def savings():
    SavingFactory(
        date=date(1970, 1, 1),
        price=125,
        fee=25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )
    SavingFactory(
        date=date(1970, 1, 1),
        price=25,
        fee=0,
        account=AccountFactory(title="Account2"),
        saving_type=SavingTypeFactory(title="Saving2"),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=125,
        fee=25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=225,
        fee=25,
        account=AccountFactory(title="Account1"),
        saving_type=SavingTypeFactory(title="Saving1"),
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=225,
        fee=25,
        account=AccountFactory(title="Account2"),
        saving_type=SavingTypeFactory(title="Saving2"),
    )


@pytest.fixture()
def savings_close():
    SavingCloseFactory(
        date=date(1999, 1, 1),
        price=25,
        fee=5,
        to_account=AccountFactory(title="Account1"),
        from_account=SavingTypeFactory(title="Saving1"),
    )
    SavingCloseFactory(
        date=date(1999, 1, 1),
        price=1,
        fee=1,
        to_account=AccountFactory(title="Account2"),
        from_account=SavingTypeFactory(title="Saving1"),
    )
    SavingCloseFactory(
        date=date(1970, 1, 1),
        price=25,
        fee=5,
        to_account=AccountFactory(title="Account1"),
        from_account=SavingTypeFactory(title="Saving1"),
    )


@pytest.fixture()
def savings_change():
    SavingChangeFactory(
        date=date(1999, 1, 1),
        price=125,
        fee=5,
        to_account=SavingTypeFactory(title="Saving2"),
        from_account=SavingTypeFactory(title="Saving1"),
    )
    SavingChangeFactory(
        date=date(1970, 1, 1),
        price=225,
        fee=15,
        to_account=SavingTypeFactory(title="Saving2"),
        from_account=SavingTypeFactory(title="Saving1"),
    )


@pytest.fixture()
def pensions():
    PensionFactory(
        price=125,
        fee=0,
        date=date(1974, 1, 1),
    )
    PensionFactory(
        price=225,
        fee=25,
        date=date(1974, 1, 1),
    )
    PensionFactory(
        price=225,
        fee=0,
        date=date(1999, 1, 1),
    )
    PensionFactory(
        price=225,
        fee=5,
        date=date(1999, 1, 1),
    )


@pytest.fixture()
def accounts_worth():
    AccountWorthFactory(
        date=datetime(1970, 1, 1, tzinfo=pytz.utc),
        price=10,
        account=AccountFactory(title="Account1"),
    )
    AccountWorthFactory(
        date=datetime(1970, 1, 1, tzinfo=pytz.utc),
        price=20,
        account=AccountFactory(title="Account2"),
    )

    AccountWorthFactory(
        date=datetime(1999, 1, 2, tzinfo=pytz.utc),
        price=3,
        account=AccountFactory(title="Account1"),
    )
    AccountWorthFactory(
        date=datetime(1999, 1, 1, tzinfo=pytz.utc),
        price=8,
        account=AccountFactory(title="Account2"),
    )


@pytest.fixture()
def savings_worth():
    SavingWorthFactory(
        date=datetime(1970, 1, 1, tzinfo=pytz.utc),
        price=10,
        saving_type=SavingTypeFactory(title="Saving1"),
    )

    SavingWorthFactory(
        date=datetime(1999, 1, 2, tzinfo=pytz.utc),
        price=15,
        saving_type=SavingTypeFactory(title="Saving1"),
    )
    SavingWorthFactory(
        date=datetime(1999, 1, 1, tzinfo=pytz.utc),
        price=6,
        saving_type=SavingTypeFactory(title="Saving2"),
    )


@pytest.fixture()
def pensions_worth():
    PensionWorthFactory(date=datetime(1974, 1, 1, tzinfo=pytz.utc), price=6)
    PensionWorthFactory(price=25)


@pytest.fixture
def lend_fixture():
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    LendFactory(date=date(1999, 1, 2), price=1, account=a1)
    LendFactory(date=date(1999, 2, 3), price=2, account=a1)
    LendFactory(date=date(1999, 3, 4), price=3, account=a2)

    LendFactory(date=date(1974, 1, 2), price=4, account=a1)
    LendFactory(date=date(1974, 2, 3), price=5, account=a1)


@pytest.fixture
def lend_return_fixture():
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    LendReturnFactory(date=date(1999, 1, 2), price=5, account=a1)
    LendReturnFactory(date=date(1999, 2, 3), price=15, account=a1)
    LendReturnFactory(date=date(1999, 3, 4), price=16, account=a2)

    LendReturnFactory(date=date(1974, 1, 2), price=35, account=a1)
    LendReturnFactory(date=date(1974, 2, 3), price=45, account=a1)
