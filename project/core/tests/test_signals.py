from datetime import datetime

import polars as pl
import pytest
from django.utils import timezone

from ...accounts.factories import AccountBalance, AccountBalanceFactory, AccountFactory
from ...pensions.factories import (
    PensionBalance,
    PensionBalanceFactory,
    PensionTypeFactory,
)
from ...savings.factories import (
    SavingBalance,
    SavingBalanceFactory,
    SavingTypeFactory,
)
from ..signals import BalanceSynchronizer

pytestmark = pytest.mark.django_db


def test_account_insert_new_records_empty_db():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=account, year=2023)
    assert record.incomes == 1000
    assert record.expenses == 500
    assert record.have == 500
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.balance == 500
    assert record.past == 0
    assert record.delta == 0


def test_account_insert_new_records():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=obj.account, year=2024)
    assert record.incomes == 2000
    assert record.expenses == 1000
    assert record.have == 1000
    assert record.latest_check == timezone.make_aware(datetime(2024, 1, 1))
    assert record.balance == 1000
    assert record.past == 0
    assert record.delta == 0


def test_account_update_existing_records():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=obj.account, year=1999)
    assert record.incomes == 2000
    assert record.expenses == 1000
    assert record.have == 1000
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 2))
    assert record.balance == 1000
    assert record.past == 1
    assert record.delta == 1


def test_account_delete_records():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

    assert AccountBalance.objects.count() == 0


def test_account_mixed_operations():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

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


def test_account_null_latest_check():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

    assert AccountBalance.objects.count() == 1
    record = AccountBalance.objects.get(account=account, year=2023)
    assert record.latest_check is None
    assert record.incomes == 1000


def test_account_empty_dataframe_deletes_all():
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
    ).lazy()

    BalanceSynchronizer(AccountBalance, df)

    assert AccountBalance.objects.count() == 0


def test_saving_insert_new_records_empty_db():
    saving_type = SavingTypeFactory()

    df = pl.DataFrame(
        {
            "category_id": [saving_type.pk],
            "year": [2023],
            "latest_check": [datetime(2023, 1, 1)],
            "past_amount": [10],
            "past_fee": [20],
            "fee": [30],
            "per_year_incomes": [40],
            "per_year_fee": [50],
            "sold": [60],
            "sold_fee": [70],
            "incomes": [80],
            "market_value": [90],
            "profit_sum": [100],
            "profit_proc": [110],
        }
    ).lazy()

    BalanceSynchronizer(SavingBalance, df)

    assert SavingBalance.objects.count() == 1

    record = SavingBalance.objects.get(saving_type=saving_type, year=2023)
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.past_amount == 10
    assert record.past_fee == 20
    assert record.fee == 30
    assert record.per_year_incomes == 40
    assert record.per_year_fee == 50
    assert record.sold == 60
    assert record.sold_fee == 70
    assert record.incomes == 80
    assert record.market_value == 90
    assert record.profit_sum == 100
    assert record.profit_proc == 110


def test_saving_insert_new_records():
    obj = SavingBalanceFactory()

    df = pl.DataFrame(
        {
            "category_id": [obj.saving_type.pk],
            "year": [2023],
            "latest_check": [datetime(2023, 1, 1)],
            "past_amount": [10],
            "past_fee": [20],
            "fee": [30],
            "per_year_incomes": [40],
            "per_year_fee": [50],
            "sold": [60],
            "sold_fee": [70],
            "incomes": [80],
            "market_value": [90],
            "profit_sum": [100],
            "profit_proc": [110],
        }
    ).lazy()

    BalanceSynchronizer(SavingBalance, df)

    assert SavingBalance.objects.count() == 1

    record = SavingBalance.objects.get(saving_type=obj.saving_type, year=2023)
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.past_amount == 10
    assert record.past_fee == 20
    assert record.fee == 30
    assert record.per_year_incomes == 40
    assert record.per_year_fee == 50
    assert record.sold == 60
    assert record.sold_fee == 70
    assert record.incomes == 80
    assert record.market_value == 90
    assert record.profit_sum == 100
    assert record.profit_proc == 110


def test_saving_delete_records():
    SavingBalanceFactory()

    df = pl.DataFrame(
        {
            "category_id": [],
            "year": [],
            "latest_check": [],
            "past_amount": [],
            "past_fee": [],
            "fee": [],
            "per_year_incomes": [],
            "per_year_fee": [],
            "sold": [],
            "sold_fee": [],
            "incomes": [],
            "market_value": [],
            "profit_sum": [],
            "profit_proc": [],
        }
    ).lazy()

    BalanceSynchronizer(SavingBalance, df)

    assert SavingBalance.objects.count() == 0


def test_saving_update_existing_records():
    obj = SavingBalanceFactory()

    df = pl.DataFrame(
        {
            "category_id": [obj.saving_type.pk],
            "year": [1999],
            "latest_check": [datetime(2023, 1, 1)],
            "past_amount": [10],
            "past_fee": [20],
            "fee": [30],
            "per_year_incomes": [40],
            "per_year_fee": [50],
            "sold": [60],
            "sold_fee": [70],
            "incomes": [80],
            "market_value": [90],
            "profit_sum": [100],
            "profit_proc": [110],
        }
    ).lazy()

    BalanceSynchronizer(SavingBalance, df)

    assert SavingBalance.objects.count() == 1

    record = SavingBalance.objects.get(saving_type=obj.saving_type, year=1999)
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.past_amount == 10
    assert record.past_fee == 20
    assert record.fee == 30
    assert record.per_year_incomes == 40
    assert record.per_year_fee == 50
    assert record.sold == 60
    assert record.sold_fee == 70
    assert record.incomes == 80
    assert record.market_value == 90
    assert record.profit_sum == 100
    assert record.profit_proc == 110


def test_saving_empty_dataframe_deletes_all():
    """Test empty DataFrame deletes all records."""
    SavingBalanceFactory(year=2023)
    SavingBalanceFactory(year=2024)

    df = pl.DataFrame(
        {
            "category_id": [],
            "year": [],
            "latest_check": [],
            "past_amount": [],
            "past_fee": [],
            "fee": [],
            "per_year_incomes": [],
            "per_year_fee": [],
            "sold": [],
            "sold_fee": [],
            "incomes": [],
            "market_value": [],
            "profit_sum": [],
            "profit_proc": [],
        }
    ).lazy()

    BalanceSynchronizer(SavingBalance, df)

    assert SavingBalance.objects.count() == 0


def test_pension_insert_new_records_empty_db():
    pension_type = PensionTypeFactory()

    df = pl.DataFrame(
        {
            "category_id": [pension_type.pk],
            "year": [2023],
            "latest_check": [datetime(2023, 1, 1)],
            "past_amount": [10],
            "past_fee": [20],
            "fee": [30],
            "per_year_incomes": [40],
            "per_year_fee": [50],
            "sold": [60],
            "sold_fee": [70],
            "incomes": [80],
            "market_value": [90],
            "profit_sum": [100],
            "profit_proc": [110],
        }
    ).lazy()

    BalanceSynchronizer(PensionBalance, df)

    assert PensionBalance.objects.count() == 1

    record = PensionBalance.objects.get(pension_type=pension_type, year=2023)
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.past_amount == 10
    assert record.past_fee == 20
    assert record.fee == 30
    assert record.per_year_incomes == 40
    assert record.per_year_fee == 50
    assert record.sold == 60
    assert record.sold_fee == 70
    assert record.incomes == 80
    assert record.market_value == 90
    assert record.profit_sum == 100
    assert record.profit_proc == 110


def test_pension_insert_new_records():
    obj = PensionBalanceFactory()

    df = pl.DataFrame(
        {
            "category_id": [obj.pension_type.pk],
            "year": [2023],
            "latest_check": [datetime(2023, 1, 1)],
            "past_amount": [10],
            "past_fee": [20],
            "fee": [30],
            "per_year_incomes": [40],
            "per_year_fee": [50],
            "sold": [60],
            "sold_fee": [70],
            "incomes": [80],
            "market_value": [90],
            "profit_sum": [100],
            "profit_proc": [110],
        }
    ).lazy()

    BalanceSynchronizer(PensionBalance, df)

    assert PensionBalance.objects.count() == 1

    record = PensionBalance.objects.get(pension_type=obj.pension_type, year=2023)
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.past_amount == 10
    assert record.past_fee == 20
    assert record.fee == 30
    assert record.per_year_incomes == 40
    assert record.per_year_fee == 50
    assert record.sold == 60
    assert record.sold_fee == 70
    assert record.incomes == 80
    assert record.market_value == 90
    assert record.profit_sum == 100
    assert record.profit_proc == 110


def test_pension_delete_records():
    PensionBalanceFactory()

    df = pl.DataFrame(
        {
            "category_id": [],
            "year": [],
            "latest_check": [],
            "past_amount": [],
            "past_fee": [],
            "fee": [],
            "per_year_incomes": [],
            "per_year_fee": [],
            "sold": [],
            "sold_fee": [],
            "incomes": [],
            "market_value": [],
            "profit_sum": [],
            "profit_proc": [],
        }
    ).lazy()

    BalanceSynchronizer(PensionBalance, df)

    assert PensionBalance.objects.count() == 0


def test_pension_update_existing_records():
    obj = PensionBalanceFactory()

    df = pl.DataFrame(
        {
            "category_id": [obj.pension_type.pk],
            "year": [1999],
            "latest_check": [datetime(2023, 1, 1)],
            "past_amount": [10],
            "past_fee": [20],
            "fee": [30],
            "per_year_incomes": [40],
            "per_year_fee": [50],
            "sold": [60],
            "sold_fee": [70],
            "incomes": [80],
            "market_value": [90],
            "profit_sum": [100],
            "profit_proc": [110],
        }
    ).lazy()

    BalanceSynchronizer(PensionBalance, df)

    assert PensionBalance.objects.count() == 1

    record = PensionBalance.objects.get(pension_type=obj.pension_type, year=1999)
    assert record.latest_check == timezone.make_aware(datetime(2023, 1, 1))
    assert record.past_amount == 10
    assert record.past_fee == 20
    assert record.fee == 30
    assert record.per_year_incomes == 40
    assert record.per_year_fee == 50
    assert record.sold == 60
    assert record.sold_fee == 70
    assert record.incomes == 80
    assert record.market_value == 90
    assert record.profit_sum == 100
    assert record.profit_proc == 110


def test_pension_empty_dataframe_deletes_all():
    """Test empty DataFrame deletes all records."""
    PensionBalanceFactory(year=2023)
    PensionBalanceFactory(year=2024)

    df = pl.DataFrame(
        {
            "category_id": [],
            "year": [],
            "latest_check": [],
            "past_amount": [],
            "past_fee": [],
            "fee": [],
            "per_year_incomes": [],
            "per_year_fee": [],
            "sold": [],
            "sold_fee": [],
            "incomes": [],
            "market_value": [],
            "profit_sum": [],
            "profit_proc": [],
        }
    ).lazy()

    BalanceSynchronizer(PensionBalance, df)

    assert PensionBalance.objects.count() == 0