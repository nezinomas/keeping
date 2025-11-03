from typing import Tuple

import polars as pl
from django.db import models
from django.db import transaction as django_transaction
from django.utils import timezone

from ...journals.models import Journal
from ...pensions import models as pension
from ...savings import models as saving

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

    def __init__(self, model: models.Model, journal: Journal, df: pl.LazyFrame) -> None:
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
        self.journal = journal
        self.df = df
        self.df_db = self._get_existing_records()

        self.sync()

    def _get_existing_records(self) -> pl.LazyFrame:
        # Select only necessary fields to reduce memory usage
        records = [
            *self.model.objects.related(self.journal).values(
                "id", self.fk_field, "year", *self.fields
            )
        ]
        if not records:
            return pl.LazyFrame()

        df_db = pl.from_dicts(records).lazy().rename({self.fk_field: "category_id"})
        if "latest_check" in df_db.collect_schema().names():
            df_db = df_db.with_columns(
                pl.col("latest_check").cast(pl.Datetime).dt.replace_time_zone(None)
            )

        return df_db

    def _identify_operations(self) -> Tuple[pl.LazyFrame, pl.LazyFrame, pl.LazyFrame]:
        empty_df = pl.LazyFrame()

        if self.df_db.limit(1).collect().is_empty():
            return self.df, empty_df, empty_df

        if self.df.limit(1).collect().is_empty():
            return empty_df, empty_df, self.df_db

        return self._insert_df(), self._update_df(), self._delete_df()

    def _delete_df(self) -> pl.LazyFrame:
        df_keys = self.df.select(self.KEY_FIELDS).unique()
        return self.df_db.join(df_keys, on=self.KEY_FIELDS, how="anti")

    def _insert_df(self) -> pl.LazyFrame:
        return self.df.join(
            self.df_db.lazy().select(self.KEY_FIELDS),
            on=self.KEY_FIELDS,
            how="anti",
        )

    def _update_df(self) -> pl.LazyFrame:
        common = self.df.join(self.df_db, on=self.KEY_FIELDS, how="inner", suffix="_db")

        return common.filter(
            pl.any_horizontal([pl.col(f) != pl.col(f"{f}_db") for f in self.fields])
        ).select(self.df.collect_schema().names())

    def _delete_records(self, data: pl.LazyFrame) -> None:
        df = data.collect()

        if df.is_empty():
            return

        category_ids = df["category_id"].unique().to_list()
        years = df["year"].unique().to_list()
        self.model.objects.filter(
            **{f"{self.fk_field}__in": category_ids, "year__in": years}
        ).delete()

    def _insert_records(self, data: pl.LazyFrame) -> None:
        df = data.collect()

        if df.is_empty():
            return

        if objects := [self._create_object(row) for row in df.to_dicts()]:
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
