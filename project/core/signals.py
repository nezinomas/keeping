from typing import Tuple

import polars as pl
from django.db import transaction as django_transaction
from django.db.models import Model, Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import make_aware

from ..accounts import models as account
from ..accounts.models import AccountBalance
from ..bookkeeping import models as bookkeeping
from ..debts import models as debt
from ..expenses import models as expense
from ..incomes import models as income
from ..pensions import models as pension
from ..savings import models as saving
from ..transactions import models as transaction
from .lib.signals import Accounts, GetData, Savings, SignalBase


# -------------------------------------------------------------------------------------
#                                                                      Accounts Signals
# -------------------------------------------------------------------------------------
@receiver(post_save, sender=income.Income)
@receiver(post_delete, sender=income.Income)
@receiver(post_save, sender=expense.Expense)
@receiver(post_delete, sender=expense.Expense)
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=transaction.Transaction)
@receiver(post_delete, sender=transaction.Transaction)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=debt.Debt)
@receiver(post_delete, sender=debt.Debt)
@receiver(post_save, sender=debt.DebtReturn)
@receiver(post_delete, sender=debt.DebtReturn)
@receiver(post_save, sender=bookkeeping.AccountWorth)
def accounts_signal(sender: object, instance: object, *args, **kwargs):
    data = accounts_data()
    objects = create_objects(account.AccountBalance, data.types, data.table)
    save_objects(account.AccountBalance, objects)


def accounts_data() -> SignalBase:
    conf = {
        "incomes": (
            income.Income,
            debt.Debt,
            debt.DebtReturn,
            transaction.Transaction,
            transaction.SavingClose,
        ),
        "expenses": (
            expense.Expense,
            debt.Debt,
            debt.DebtReturn,
            transaction.Transaction,
            saving.Saving,
        ),
        "have": (bookkeeping.AccountWorth,),
        "types": (account.Account,),
    }
    return Accounts(GetData(conf))


# -------------------------------------------------------------------------------------
#                                                                       Savings Signals
# -------------------------------------------------------------------------------------
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=transaction.SavingChange)
@receiver(post_delete, sender=transaction.SavingChange)
@receiver(post_save, sender=bookkeeping.SavingWorth)
def savings_signal(sender: object, instance: object, *args, **kwargs):
    data = savings_data()
    objects = create_objects(saving.SavingBalance, data.types, data.table)
    save_objects(saving.SavingBalance, objects)


def savings_data() -> SignalBase:
    conf = {
        "incomes": (
            saving.Saving,
            transaction.SavingChange,
        ),
        "expenses": (
            transaction.SavingClose,
            transaction.SavingChange,
        ),
        "have": (bookkeeping.SavingWorth,),
        "types": (saving.SavingType,),
    }
    return Savings(GetData(conf))


# -------------------------------------------------------------------------------------
#                                                                      Pensions Signals
# -------------------------------------------------------------------------------------
@receiver(post_save, sender=pension.Pension)
@receiver(post_delete, sender=pension.Pension)
@receiver(post_save, sender=bookkeeping.PensionWorth)
def pensions_signal(sender: object, instance: object, *args, **kwargs):
    data = pensions_data()
    objects = create_objects(pension.PensionBalance, data.types, data.table)
    save_objects(pension.PensionBalance, objects)


def pensions_data() -> SignalBase:
    conf = {
        "incomes": (pension.Pension,),
        "have": (bookkeeping.PensionWorth,),
        "types": (pension.PensionType,),
    }
    return Savings(GetData(conf))


# -------------------------------------------------------------------------------------
#                                                                        Common methods
# -------------------------------------------------------------------------------------
def create_objects(balance_model: Model, categories: dict, data: list[dict]):
    fields = balance_model._meta.get_fields()
    fk_field = [f.name for f in fields if (f.many_to_one)][0]
    objects = []
    for x in data:
        # extract account/saving_type/pension_type id from dict
        cid = x.pop("category_id")
        # drop latest_check if empty
        if not x["latest_check"]:
            x.pop("latest_check")
        else:
            x["latest_check"] = make_aware(x["latest_check"])
        # create fk_field account|saving_type|pension_type object
        x[fk_field] = categories.get(cid)
        # create AccountBalance/SavingBalance/PensionBalance object
        objects.append(balance_model(**x))
    return objects


def save_objects(balance_model, objects):
    # delete all records
    balance_model.objects.related().delete()
    # bulk create
    balance_model.objects.bulk_create(objects)


class BalanceSynchronizer:
    """Synchronizes AccountBalance model with Polars DataFrame efficiently."""

    FIELDS = ["incomes", "expenses", "have", "latest_check", "balance", "past", "delta"]
    KEY_FIELDS = ["category_id", "year"]

    def __init__(self, df: pl.DataFrame) -> None:
        self.df = df.select(
            self.KEY_FIELDS + self.FIELDS
        )  # Select only necessary columns
        self.df_db, self.df_map = self._get_existing_records()
        self.sync()

    def _get_existing_records(self) -> Tuple[pl.DataFrame, pl.DataFrame]:
        """Fetch existing records as a Polars DataFrame with minimal data."""
        # Select only necessary fields to reduce memory usage
        records = AccountBalance.objects.related().values(
            "id", "account_id", "year", *self.FIELDS
        )
        if not records:
            return pl.DataFrame(), pl.DataFrame()

        df_db = pl.DataFrame(list(records)).rename({"account_id": "category_id"})
        df_map = df_db.select(["id", "year", "category_id"])
        df_db = df_db.drop("id")

        return df_db, df_map

    def _identify_operations(self) -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
        """Identify records to insert, update, and delete using efficient Polars joins."""
        if self.df_db.is_empty():
            return self.df, pl.DataFrame(), pl.DataFrame()

        if self.df.is_empty():
            return pl.DataFrame(), pl.DataFrame(), self.df_db

        # Use lazy evaluation for joins
        df_keys = self.df.select(self.KEY_FIELDS).unique()

        # Inserts: records in df but not in db
        inserts = self.df.join(
            self.df_db.select(self.KEY_FIELDS),
            on=self.KEY_FIELDS,
            how="anti",
        )

        # Updates: records in both, with differing fields
        common = self.df.join(
            self.df_db, on=self.KEY_FIELDS, how="inner", suffix="_db"
        ).lazy()

        updates = (
            common.filter(
                pl.any_horizontal([pl.col(f) != pl.col(f"{f}_db") for f in self.FIELDS])
            )
            .select(self.df.columns)
            .collect()
        )

        # Deletes: records in db but not in df
        deletes = self.df_db.join(df_keys, on=self.KEY_FIELDS, how="anti")

        return inserts, updates, deletes

    def _delete_records(self, deletes: pl.DataFrame) -> None:
        """Delete records efficiently using bulk conditions."""
        if deletes.is_empty():
            return

        if delete_ids := self.df_map.join(
            deletes.select(self.KEY_FIELDS), on=self.KEY_FIELDS, how="inner"
        )["id"].to_list():
            AccountBalance.objects.filter(id__in=delete_ids).delete()

    def _insert_records(self, inserts: pl.DataFrame) -> None:
        """Insert records using bulk_create with batch processing."""
        if inserts.is_empty():
            return

        batch_size = 1000  # Adjustable based on system constraints
        to_insert = []

        for row in inserts.iter_rows(named=True):
            to_insert.append(
                AccountBalance(
                    account_id=row["category_id"],
                    year=row["year"],
                    incomes=row["incomes"],
                    expenses=row["expenses"],
                    have=row["have"],
                    latest_check=timezone.make_aware(row["latest_check"])
                    if row["latest_check"]
                    else None,
                    balance=row["balance"],
                    past=row["past"],
                    delta=row["delta"],
                )
            )

            if len(to_insert) >= batch_size:
                AccountBalance.objects.bulk_create(to_insert)
                to_insert = []

        if to_insert:
            AccountBalance.objects.bulk_create(to_insert)

    def _update_records(self, updates: pl.DataFrame) -> None:
        """Update records using bulk_update with batch processing."""
        if updates.is_empty():
            return

        updates_with_id = updates.join(self.df_map, on=self.KEY_FIELDS, how="left")

        to_update = [
            AccountBalance(
                id=row["id"],
                account_id=row["category_id"],
                year=row["year"],
                incomes=row["incomes"],
                expenses=row["expenses"],
                have=row["have"],
                latest_check=(
                    timezone.make_aware(row["latest_check"])
                    if row["latest_check"]
                    else None
                ),
                balance=row["balance"],
                past=row["past"],
                delta=row["delta"],
            )
            for row in updates_with_id.iter_rows(named=True)
        ]
        if to_update:
            AccountBalance.objects.bulk_update(to_update, self.FIELDS)

    @django_transaction.atomic
    def sync(self) -> None:
        """Synchronize database with DataFrame in a single transaction."""
        inserts, updates, deletes = self._identify_operations()
        self._delete_records(deletes)
        self._insert_records(inserts)
        self._update_records(updates)
