from abc import ABC, abstractmethod

import polars as pl

from ...users.models import User

KEYS = ["category_id", "year"]


class BalanceSources:
    def __init__(self, user: User, conf: dict):
        self.incomes = self._read(user, conf, "incomes")
        self.expenses = self._read(user, conf, "expenses")
        self.moves = self._read(user, conf, "moves")
        self.have = self._read(user, conf, "have")
        self.types = self._read(user, conf, "types")

    @staticmethod
    def _read(user: User, conf: dict, key: str) -> list:
        return [row for source in conf.get(key, ()) for row in source(user)]


class BalanceRows(ABC):
    def __init__(self, sources: BalanceSources):
        self._closed_years = self._make_closed_years(sources.types)
        self._rows = self._build_rows(sources)

    @property
    def schema(self) -> dict:
        return {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "incomes": pl.Int32,
            "expenses": pl.Int32,
        }

    @property
    def rows(self) -> pl.LazyFrame:
        return self._rows

    @abstractmethod
    def _join_sources(self, sources: BalanceSources) -> pl.LazyFrame: ...

    @abstractmethod
    def _make_table(self, df: pl.LazyFrame) -> pl.LazyFrame: ...

    def _build_rows(self, sources: BalanceSources) -> pl.LazyFrame:
        df = self._join_sources(sources)

        # an empty journal has no years to lay the grid over
        if not (sources.incomes or sources.expenses or sources.have):
            return df

        if not sources.types:
            raise ValueError("a journal's entries need their owners")

        return self._make_table(df)

    def _make_df(self, arr: list[dict]) -> pl.LazyFrame:
        return (
            pl.from_dicts(arr, schema=self.schema)
            .lazy()
            .with_columns(
                [pl.col("incomes").fill_null(0), pl.col("expenses").fill_null(0)]
            )
            .group_by(KEYS)
            .agg(pl.all().sum())
        )

    @staticmethod
    def _make_have(have: list[dict]) -> pl.LazyFrame:
        schema = {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "have": pl.UInt32,
            "latest_check": pl.Datetime,
        }
        return pl.LazyFrame(have, schema=schema)

    @staticmethod
    def _make_closed_years(types: list) -> pl.LazyFrame:
        schema = {"category_id": pl.UInt16, "closed": pl.UInt16}
        return pl.LazyFrame(
            [{"category_id": x.pk, "closed": x.closed} for x in types], schema=schema
        )

    @staticmethod
    def _full_join(left: pl.LazyFrame, right: pl.LazyFrame) -> pl.LazyFrame:
        # a full join keeps a year that only one side has
        return left.join(right, on=KEYS, how="full", coalesce=True, nulls_equal=True)

    def _fill_missing_past_future_rows(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.pipe(self._create_year_grid)
            .with_columns(
                pl.col("have", "latest_check")
                .fill_null(strategy="forward")
                .over("category_id"),
            )
            .with_columns(pl.all().exclude("latest_check").fill_null(0))
        )

    def _create_year_grid(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            self._owner_years(df)
            .join(df, on=KEYS, how="left")
            .pipe(self._drop_closed_years)
            .select(df.collect_schema().names())
            .sort(KEYS)
        )

    def _owner_years(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.group_by("category_id")
            .agg(min_year=pl.col("year").min())
            .join(self._journal_years(df), how="cross")
            .filter(pl.col("year") >= pl.col("min_year"))
            .select(KEYS)
        )

    @staticmethod
    def _journal_years(df: pl.LazyFrame) -> pl.LazyFrame:
        first_year, last_year = (
            df.select(first=pl.col("year").min(), last=pl.col("year").max())
            .collect()
            .row(0)
        )
        return pl.LazyFrame({"year": range(first_year, last_year + 2)})

    def _drop_closed_years(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.join(self._closed_years, on="category_id", how="inner").filter(
            pl.col("closed").is_null() | (pl.col("year") <= pl.col("closed"))
        )
