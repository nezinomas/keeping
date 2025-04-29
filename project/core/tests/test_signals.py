from datetime import datetime

import polars as pl
import pytest
from django.utils import timezone

from ...accounts.factories import AccountBalanceFactory, AccountFactory
from ...accounts.models import AccountBalance
from ..signals import BalanceSynchronizer, create_objects

pytestmark = pytest.mark.django_db


def test_create_objects():
    account = AccountFactory.build()

    data = [
        dict(
            category_id=1,
            year=1999,
            past=1,
            incomes=2,
            expenses=3,
            balance=4,
            have=5,
            delta=6,
            latest_check=datetime(1999, 1, 1, 3, 2, 1),
        )
    ]
    actual = create_objects(AccountBalance, {1: account}, data)[0]

    assert actual.account == account
    assert actual.year == 1999
    assert actual.past == 1
    assert actual.incomes == 2
    assert actual.expenses == 3
    assert actual.balance == 4
    assert actual.have == 5
    assert actual.delta == 6
    assert actual.latest_check == timezone.make_aware(datetime(1999, 1, 1, 3, 2, 1))


def test_insert_new_records_empty_db():
    account = AccountFactory()

    df = pl.DataFrame(
        {
            "category_id": [account.pk],
            "year": [2023],
            "incomes": [1000],
            "expenses": [500],
            "have": [500],
            "latest_check": [datetime(2023, 1, 1)],
            "balance": [500],
            "past": [0],
            "delta": [0],
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=account, year=2023)
    assert record.incomes == 1000
    assert record.expenses == 500
    assert record.have == 500
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.balance == 500
    assert record.past == 0
    assert record.delta == 0


@pytest.mark.django_db
def test_insert_new_records():
    obj = AccountBalanceFactory()

    """Test inserting new records from DataFrame."""
    df = pl.DataFrame(
        {
            "category_id": [obj.account.pk],
            "year": [2024],
            "incomes": [2000],
            "expenses": [1000],
            "have": [1000],
            "latest_check": [datetime(2024, 1, 1)],
            "balance": [1000],
            "past": [0],
            "delta": [0],
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=obj.account, year=2024)
    assert record.incomes == 2000
    assert record.expenses == 1000
    assert record.have == 1000
    assert record.latest_check == timezone.make_aware(datetime(2024, 1, 1))
    assert record.balance == 1000
    assert record.past == 0
    assert record.delta == 0


@pytest.mark.django_db
def test_update_existing_records():
    obj = AccountBalanceFactory()
    """Test updating existing records from DataFrame."""
    df = pl.DataFrame(
        {
            "category_id": [obj.account.pk],
            "year": [1999],
            "incomes": [2000],  # Updated
            "expenses": [1000],  # Updated
            "have": [1000],  # Updated
            "latest_check": [datetime(2023, 1, 2)],  # Updated
            "balance": [1000],  # Updated
            "past": [1],  # Updated
            "delta": [1],  # Updated
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=obj.account, year=1999)
    assert record.incomes == 2000
    assert record.expenses == 1000
    assert record.have == 1000
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 2))
    assert record.balance == 1000
    assert record.past == 1
    assert record.delta == 1


@pytest.mark.django_db
def test_delete_records():
    AccountBalanceFactory()

    """Test deleting records not in DataFrame."""
    df = pl.DataFrame(
        {
            "category_id": [],
            "year": [],
            "incomes": [],
            "expenses": [],
            "have": [],
            "latest_check": [],
            "balance": [],
            "past": [],
            "delta": [],
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 0


def test_mixed_operations():
    """Test simultaneous insert, update, and delete."""
    account = AccountFactory()
    # Existing record to update
    AccountBalanceFactory(year=2023, account=account)
    # Existing record to delete
    AccountBalanceFactory(year=2022, account=account)

    df = pl.DataFrame(
        {
            "category_id": [account.pk, account.pk],
            "year": [2023, 2024],  # 2023: update, 2024: insert
            "incomes": [2000, 3000],
            "expenses": [1000, 1500],
            "have": [1000, 1500],
            "latest_check": [datetime(2023, 1, 2), datetime(2024, 1, 1)],
            "balance": [1000, 1500],
            "past": [1, 0],
            "delta": [1, 0],
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 2
    # Check updated record
    record_2023 = AccountBalance.objects.get(account=account, year=2023)
    assert record_2023.incomes == 2000
    assert record_2023.latest_check == timezone.make_aware(datetime(2023, 1, 2))
    # Check inserted record
    record_2024 = AccountBalance.objects.get(account=account, year=2024)
    assert record_2024.incomes == 3000
    assert record_2024.latest_check == timezone.make_aware(datetime(2024, 1, 1))
    # Check deleted record
    assert not AccountBalance.objects.filter(account=account, year=2022).exists()


def test_null_latest_check():
    account = AccountFactory()
    """Test handling null latest_check in DataFrame."""
    df = pl.DataFrame(
        {
            "category_id": [account.pk],
            "year": [2023],
            "incomes": [1000],
            "expenses": [500],
            "have": [500],
            "latest_check": [None],
            "balance": [500],
            "past": [0],
            "delta": [0],
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=account, year=2023)
    assert record.latest_check is None
    assert record.incomes == 1000


def test_empty_dataframe_deletes_all():
    """Test empty DataFrame deletes all records."""
    AccountBalanceFactory(year=2023)
    AccountBalanceFactory(year=2024)

    df = pl.DataFrame(
        {
            "category_id": [],
            "year": [],
            "incomes": [],
            "expenses": [],
            "have": [],
            "latest_check": [],
            "balance": [],
            "past": [],
            "delta": [],
        }
    )

    BalanceSynchronizer(df)

    assert AccountBalance.objects.count() == 0
