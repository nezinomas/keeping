import polars as pl
from django.db import transaction as django_transaction
from django.utils import timezone

from ...users.models import User

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
    "sold_since_check",
]


def _is_empty(frame: pl.LazyFrame) -> bool:
    return frame.limit(1).collect().is_empty()


class BalanceSynchronizer:
    KEY_FIELDS = ["category_id", "year"]

    def __init__(self, model_service_class, user: User, df: pl.LazyFrame) -> None:
        self.model_service_class = model_service_class
        self.user = user

        service = model_service_class(self.user)

        self.model = service.objects.model
        self.fk_field = self.model._meta.get_field(self.model.fund_field).attname
        self.fields = self.model.sync_fields

        self.df = df
        self.df_db = self._get_existing_records()

        self.sync()

    def _get_existing_records(self) -> pl.LazyFrame:
        records = [
            *self.model_service_class(self.user).objects.values(
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

    def _identify_operations(self) -> tuple[pl.LazyFrame, pl.LazyFrame, pl.LazyFrame]:
        empty_df = pl.LazyFrame()

        if _is_empty(self.df_db):
            return self.df, empty_df, empty_df

        if _is_empty(self.df):
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
            pl.any_horizontal(
                [pl.col(f).ne_missing(pl.col(f"{f}_db")) for f in self.fields]
            )
        ).select(self.df.collect_schema().names())

    def _delete_records(self, data: pl.LazyFrame) -> None:
        df = data.collect()

        if df.is_empty():
            return

        self.model_service_class(self.user).objects.filter(
            id__in=df["id"].to_list()
        ).delete()

    def _insert_records(self, data: pl.LazyFrame) -> None:
        df = data.collect()

        if df.is_empty():
            return

        objects = [self.model(**self._row_fields(row)) for row in df.to_dicts()]
        self.model_service_class(self.user).objects.bulk_create(objects)

    def _update_records(self, data: pl.LazyFrame) -> None:
        if _is_empty(data):
            return

        df_map = self.df_db.select(["id", "year", "category_id"])

        updates_with_id = (
            data.join(df_map, on=self.KEY_FIELDS, how="left").collect().to_dicts()
        )

        objects = [
            self.model(id=row["id"], **self._row_fields(row)) for row in updates_with_id
        ]
        self.model_service_class(self.user).objects.bulk_update(objects, self.fields)

    def _row_fields(self, row: dict) -> dict:
        fields = {field: row[field] for field in self.fields}
        fields["latest_check"] = (
            timezone.make_aware(row["latest_check"]) if row["latest_check"] else None
        )
        fields[self.fk_field] = row["category_id"]
        fields["year"] = row["year"]

        return fields

    def sync(self) -> None:
        inserts, updates, deletes = self._identify_operations()

        with django_transaction.atomic():
            self._delete_records(deletes)
            self._insert_records(inserts)
            self._update_records(updates)
