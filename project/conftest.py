from datetime import date

import hypothesis
import pytest
from django.conf import settings
from django.db.backends.signals import connection_created
from django.utils import translation

from .accounts.tests.factories import AccountFactory
from .expenses.tests.factories import ExpenseFactory
from .incomes.tests.factories import IncomeFactory
from .pensions.tests.factories import PensionFactory, PensionTypeFactory
from .savings.tests.factories import SavingFactory, SavingTypeFactory
from .transactions.tests.factories import (
    SavingCloseFactory,
    TransactionFactory,
)
from .users.tests.factories import UserFactory

hypothesis.settings.register_profile("dev", max_examples=20, deadline=None)
hypothesis.settings.register_profile("gate", max_examples=100, deadline=None)
hypothesis.settings.load_profile("dev")


def _user(request, **kwargs):
    if "django_db" not in request.keywords:
        return UserFactory.build(**kwargs)

    user = UserFactory(**kwargs)
    user.journal.first_record = date(1999, 1, 1)
    user.journal.save()

    return user


@pytest.fixture()
def main_user(request):
    return _user(request)


@pytest.fixture(autouse=True)
def _main_user_unless_disabled(request):
    if "no_main_user" not in request.keywords:
        request.getfixturevalue("main_user")


@pytest.fixture(autouse=True)
def reset_language():
    yield

    translation.activate(settings.LANGUAGE_CODE)


@pytest.fixture()
def second_user(request):
    return _user(request, username="X", email="x@x.xx")


@pytest.fixture()
def fake_request(rf, db):
    request = rf.get("/fake/")
    request.user = UserFactory()

    return request


@pytest.fixture()
def client_logged(client, main_user):
    client.force_login(main_user)
    return client


def _sqlite_format(value, decimals, locale):
    """SQLite has no FORMAT(X, D, locale); this stands in for MariaDB's."""
    if value is None:
        return None
    try:
        formatted = f"{float(value):,.{int(decimals)}f}"
    except (ValueError, TypeError):
        return str(value)

    if locale == "lt_LT":
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


@pytest.fixture(scope="session", autouse=True)
def fix_sqlite_format_function():
    def register_functions(sender, connection, **kwargs):
        if connection.vendor == "sqlite":
            connection.connection.create_function("FORMAT", 3, _sqlite_format)

    connection_created.connect(register_functions)

    yield

    connection_created.disconnect(register_functions)


def _two_accounts():
    return AccountFactory(title="Account1"), AccountFactory(title="Account2")


@pytest.fixture()
def incomes():
    a1, a2 = _two_accounts()

    IncomeFactory(price=525, date=date(1970, 1, 1), account=a1)
    IncomeFactory(price=225, date=date(1970, 1, 1), account=a2)
    IncomeFactory(price=225, date=date(1970, 1, 31), account=a2)
    IncomeFactory(price=325, date=date(1999, 1, 1), account=a1)
    IncomeFactory(price=225, date=date(1999, 1, 1), account=a2)
    IncomeFactory(price=125, date=date(1999, 2, 1), account=a2)


@pytest.fixture()
def expenses():
    a1, a2 = _two_accounts()

    ExpenseFactory(date=date(1999, 1, 1), price=25, account=a1)
    ExpenseFactory(date=date(1999, 1, 1), price=25, account=a1)
    ExpenseFactory(date=date(1999, 12, 1), price=125, account=a2)
    ExpenseFactory(date=date(1970, 1, 1), price=125, account=a1)
    ExpenseFactory(date=date(1970, 1, 1), price=125, account=a1)
    ExpenseFactory(date=date(1970, 1, 1), price=225, account=a2)


@pytest.fixture()
def expenses_january():
    a1, a2 = _two_accounts()

    ExpenseFactory(
        date=date(1999, 1, 1),
        price=25,
        account=a1,
        exception=True,
    )
    ExpenseFactory(date=date(1999, 1, 1), price=25, account=a1)
    ExpenseFactory(date=date(1999, 1, 11), price=25, account=a1)
    ExpenseFactory(date=date(1999, 1, 11), price=25, account=a1)
    ExpenseFactory(date=date(1970, 1, 1), price=225, account=a2)


@pytest.fixture()
def transactions():
    a1, a2 = _two_accounts()

    TransactionFactory(
        date=date(1999, 1, 1),
        price=225,
        from_account=a1,
        to_account=a2,
    )
    TransactionFactory(
        date=date(1999, 1, 1),
        price=225,
        from_account=a1,
        to_account=a2,
    )
    TransactionFactory(
        date=date(1999, 1, 1),
        price=325,
        from_account=a2,
        to_account=a1,
    )
    TransactionFactory(
        date=date(1970, 1, 1),
        price=125,
        from_account=a1,
        to_account=a2,
    )
    TransactionFactory(
        date=date(1970, 1, 1),
        price=525,
        from_account=a2,
        to_account=a1,
    )


@pytest.fixture()
def savings():
    a1, a2 = _two_accounts()
    s1 = SavingTypeFactory(title="Saving1")
    s2 = SavingTypeFactory(title="Saving2")

    SavingFactory(
        date=date(1970, 1, 1),
        price=125,
        fee=25,
        account=a1,
        saving_type=s1,
    )
    SavingFactory(
        date=date(1970, 1, 1),
        price=25,
        fee=0,
        account=a2,
        saving_type=s2,
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=125,
        fee=25,
        account=a1,
        saving_type=s1,
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=225,
        fee=25,
        account=a1,
        saving_type=s1,
    )
    SavingFactory(
        date=date(1999, 1, 1),
        price=225,
        fee=25,
        account=a2,
        saving_type=s2,
    )


@pytest.fixture()
def savings_close():
    a1, a2 = _two_accounts()
    s1 = SavingTypeFactory(title="Saving1")

    SavingCloseFactory(
        date=date(1999, 1, 1),
        price=25,
        fee=5,
        to_account=a1,
        from_account=s1,
    )
    SavingCloseFactory(
        date=date(1999, 1, 1),
        price=1,
        fee=1,
        to_account=a2,
        from_account=s1,
    )
    SavingCloseFactory(
        date=date(1970, 1, 1),
        price=25,
        fee=5,
        to_account=a1,
        from_account=s1,
    )


@pytest.fixture()
def pensions():
    p = PensionTypeFactory(title="Pension1")

    PensionFactory(
        price=125,
        fee=0,
        date=date(1974, 1, 1),
        pension_type=p,
    )
    PensionFactory(
        price=225,
        fee=25,
        date=date(1974, 1, 1),
        pension_type=p,
    )
    PensionFactory(
        price=225,
        fee=0,
        date=date(1999, 1, 1),
        pension_type=p,
    )
    PensionFactory(
        price=225,
        fee=5,
        date=date(1999, 1, 1),
        pension_type=p,
    )
