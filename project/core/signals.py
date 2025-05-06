from typing import Tuple

import polars as pl
from django.db import transaction as django_transaction
from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from ..accounts import models as account
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
    BalanceSynchronizer(account.AccountBalance, data.df)


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
    BalanceSynchronizer(saving.SavingBalance, data.df)


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
    BalanceSynchronizer(pension.PensionBalance, data.df)


def pensions_data() -> SignalBase:
    conf = {
        "incomes": (pension.Pension,),
        "have": (bookkeeping.PensionWorth,),
        "types": (pension.PensionType,),
    }
    return Savings(GetData(conf))


# -------------------------------------------------------------------------------------
#                                                                      DB Synchronizer
# -------------------------------------------------------------------------------------

ACCOUNT_FIELDS = [
    "incomes",
    "expenses",
    "have",
    "latest_check",
    "balance",
    "past",
    "delta",
]

SAVING_FIELDS = [
    "latest_check",
    "past_amount",
    "past_fee",
    "fee",
    "per_year_incomes",
    "per_year_fee",
    "sold",
    "sold_fee",
    "incomes",
    "market_value",
    "profit_sum",
    "profit_proc",
]


class BalanceSynchronizer:
    KEY_FIELDS = ["category_id", "year"]

    def __init__(self, model, df: pl.LazyFrame) -> None:
        match model:
            case saving.SavingBalance:
                self.fk_field = "saving_type_id"
                self.fields = SAVING_FIELDS

            case pension.PensionBalance:
                self.fk_field = "pension_type_id"
                self.fields = SAVING_FIELDS

            case _:
                self.fk_field = "account_id"
                self.fields = ACCOUNT_FIELDS

        self.model = model
        self.df = df
        self.df_db = self._get_existing_records()

        self.sync()

    def _get_existing_records(self) -> pl.LazyFrame:
        # Select only necessary fields to reduce memory usage
        records = [
            *self.model.objects.related().values(
                "id", self.fk_field, "year", *self.fields
            )
        ]
        if not records:
            return pl.DataFrame().lazy()

        df_db = pl.from_dicts(records).lazy().rename({self.fk_field: "category_id"})
        if "latest_check" in df_db.columns:
            df_db = df_db.with_columns(
                pl.col("latest_check").cast(pl.Datetime).dt.replace_time_zone(None)
            )

        return df_db

    def _identify_operations(self) -> Tuple[pl.LazyFrame, pl.LazyFrame, pl.LazyFrame]:
        if self.df_db.limit(1).collect().is_empty():
            return self.df, pl.DataFrame().lazy(), pl.DataFrame().lazy()

        if self.df.limit(1).collect().is_empty():
            return pl.DataFrame().lazy(), pl.DataFrame().lazy(), self.df_db

        return self._insert_df(), self._update_df(), self._delete_df()

    def _delete_df(self):
        df_keys = self.df.select(self.KEY_FIELDS).unique()
        return self.df_db.join(df_keys, on=self.KEY_FIELDS, how="anti")

    def _insert_df(self):
        return self.df.join(
            self.df_db.lazy().select(self.KEY_FIELDS),
            on=self.KEY_FIELDS,
            how="anti",
        )

    def _update_df(self):
        common = self.df.join(self.df_db, on=self.KEY_FIELDS, how="inner", suffix="_db")

        return common.filter(
            pl.any_horizontal([pl.col(f) != pl.col(f"{f}_db") for f in self.fields])
        ).select(self.df.columns)

    def _delete_records(self, data: pl.LazyFrame) -> None:
        data = data.collect()

        if data.is_empty():
            return

        category_ids = data["category_id"].unique().to_list()
        years = data["year"].unique().to_list()
        self.model.objects.filter(
            **{f"{self.fk_field}__in": category_ids, "year__in": years}
        ).delete()

    def _insert_records(self, data: pl.LazyFrame) -> None:
        data = data.collect()

        if data.is_empty():
            return

        if objects := [self._create_object(row) for row in data.to_dicts()]:
            self.model.objects.bulk_create(objects)

    def _update_records(self, data: pl.LazyFrame) -> None:
        if data.limit(1).collect().is_empty():
            return

        df_map = self.df_db.select(["id", "year", "category_id"])

        updates_with_id = (
            data.join(df_map, on=self.KEY_FIELDS, how="left").collect().to_dicts()
        )

        if objects := [
            self._create_object(row, update=True) for row in updates_with_id
        ]:
            self.model.objects.bulk_update(objects, self.fields)

    def _create_object(self, row: dict, update: bool = False):
        """Create an self.model object from a row."""
        fields = {field: row[field] for field in self.fields}
        fields["latest_check"] = (
            timezone.make_aware(row["latest_check"]) if row["latest_check"] else None
        )
        fields[self.fk_field] = row["category_id"]
        fields["year"] = row["year"]

        # Set the ID from database for updates
        if update:
            fields["id"] = row["id"]

        return self.model(**fields)

    def sync(self) -> None:
        inserts, updates, deletes = self._identify_operations()

        with django_transaction.atomic():
            self._delete_records(deletes)
            self._insert_records(inserts)
            self._update_records(updates)
