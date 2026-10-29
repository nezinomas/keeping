from abc import ABC, abstractmethod

import polars as pl

from ...users.models import User


class GetData:
    def __init__(self, user: User, conf: dict):
        self.incomes = list(self._get_data(user, conf.get("incomes", ())))
        self.expenses = list(self._get_data(user, conf.get("expenses", ())))
        self.moves = list(self._get_data(user, conf.get("moves", ())))
        self.have = list(self._get_data(user, conf.get("have", ())))
        self.types = list(self._get_data(user, conf.get("types", ())))

    @staticmethod
    def _get_data(user: User, sources: tuple):
        for source_callable in sources:
            yield from source_callable(user)


class SignalBase(ABC):
    @property
    def schema(self) -> dict:
        return {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "incomes": pl.Int32,
            "expenses": pl.Int32,
        }

    @property
    def df(self) -> pl.LazyFrame:
        return self._table

    @abstractmethod
    def make_table(self, df: pl.LazyFrame) -> pl.LazyFrame: ...

    def _build_table(self, data: GetData, df: pl.LazyFrame) -> pl.LazyFrame:
        # an empty journal has no years to lay the grid over
        if not (data.incomes or data.expenses or data.have):
            return df

        return self.make_table(df)

    def _make_df(self, arr: list[dict]) -> pl.LazyFrame:
        return (
            pl.from_dicts(arr, schema=self.schema)
            .lazy()
            .with_columns(
                [pl.col("incomes").fill_null(0), pl.col("expenses").fill_null(0)]
            )
            .group_by(["category_id", "year"])
            .agg(pl.all().sum())
        )

    def _make_have(self, have: list[dict]) -> pl.LazyFrame:
        schema = {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "have": pl.UInt32,
            "latest_check": pl.Datetime,
        }
        return pl.LazyFrame(have, schema=schema)

    def _make_moves(self, moves: list[dict]) -> pl.LazyFrame:
        schema = {"category_id": pl.UInt16, "date": pl.Date, "price": pl.Int32}
        return pl.LazyFrame(moves, schema=schema).with_columns(
            year=pl.col("date").dt.year().cast(pl.UInt16)
        )

    def _closed_years(self) -> pl.LazyFrame:
        return pl.from_dicts(
            [{"category_id": x.pk, "closed": x.closed} for x in self._types]
        ).lazy()

    def _create_year_grid(self, df: pl.LazyFrame) -> pl.LazyFrame:
        years_ranges = df.group_by("category_id").agg(min_year=pl.col("year").min())

        first_year, last_year = (
            df.select(first=pl.col("year").min(), last=pl.col("year").max())
            .collect()
            .row(0)
        )

        years_df = pl.LazyFrame({"year": range(first_year, last_year + 2)})

        return (
            years_ranges.join(years_df, how="cross")
            .filter(pl.col("year") >= pl.col("min_year"))
            .select(["category_id", "year"])
            .join(df, on=["category_id", "year"], how="left")
            .join(self._closed_years(), on="category_id", how="inner")
            .filter(pl.col("closed").is_null() | (pl.col("year") <= pl.col("closed")))
            .select(df.collect_schema().names())
        )
