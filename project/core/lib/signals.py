import itertools as it
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import polars as pl


@dataclass
class GetData:
    conf: dict[tuple] = field(default_factory=dict)
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    have: list[dict] = field(init=False, default_factory=list)
    types: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = self._get_data(self.conf.get("incomes"), "incomes")
        self.expenses = self._get_data(self.conf.get("expenses"), "expenses")
        self.have = list(self._get_data(self.conf.get("have"), "have"))
        self.types = list(self._get_data(self.conf.get("types"), "related"))

    def _get_data(self, models: tuple, method: str):
        if not models:
            return

        for model in models:
            _method = getattr(model.objects, method, None)
            if callable(_method):
                if _qs := _method():
                    yield from _qs


class SignalBase(ABC):
    signal_type = None

    @property
    def types(self) -> dict:
        return {category.id: category for category in self._types}

    @property
    def df(self) -> pl.LazyFrame:
        return self._table

    @abstractmethod
    def make_table(self, df: pl.LazyFrame) -> pl.LazyFrame: ...

    def _make_df(self, arr: list[dict]) -> pl.LazyFrame:
        schema = {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "incomes": pl.Int32,
            "expenses": pl.Int32,
        }

        if self.signal_type == "savings":
            schema |= {"fee": pl.Int32}

        if not arr:
            return pl.LazyFrame(arr, schema=schema)

        return (
            pl.from_dicts(arr, schema=schema)
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

    def _create_year_grid(self, df: pl.LazyFrame) -> pl.Expr:
        # Get min_year per category_id
        years_ranges = df.group_by("category_id").agg(min_year=pl.col("year").min())

        # Create a LazyFrame of all years from 0 to global_max_year + 1
        global_max_year = df.select(pl.col("year").max()).collect().item()
        global_min_year = df.select(pl.col("year").min()).collect().item()

        years_df = pl.LazyFrame({"year": range(global_min_year, global_max_year + 2)})

        #  lazyframe of categories with closed dates
        closed = pl.from_dicts(
            [{"category_id": x.pk, "closed": x.closed} for x in self._types]
        ).lazy()

        return (
            years_ranges.join(years_df, how="cross")
            .filter(pl.col("year") >= pl.col("min_year"))
            .select(["category_id", "year"])
            .join(df, on=["category_id", "year"], how="left")
            .join(closed, on="category_id", how="inner")
            .filter(
                (pl.col("closed").is_null())  # Keep rows where closed is null
                | (pl.col("year") <= pl.col("closed"))  # or year < closed
            )
            .select(df.collect_schema().names())
        )


class Accounts(SignalBase):
    signal_type = "accounts"

    def __init__(self, data: GetData):
        _df = self._make_df(it.chain(data.incomes, data.expenses))
        _hv = self._make_have(data.have)
        _df = self._join_df(_df, _hv)

        self._types = data.types

        try:
            self._table = self.make_table(_df)
        except TypeError:
            self._table = _df

    def _missing_and_past_values(self, df: pl.LazyFrame) -> pl.LazyFrame:
        numeric_columns = [
            col for col, _ in df.collect_schema().items() if col != "latest_check"
        ]

        return (
            df.pipe(self._create_year_grid)
            .with_columns(
                pl.col("latest_check")
                .fill_null(strategy="forward")
                .over("category_id"),
                pl.col("have")
                .fill_null(strategy="forward")
                .over("category_id")
                .alias("have_alt"),
            )
            .drop("have")
            .rename({"have_alt": "have"})
            .with_columns(
                balance=(pl.col("incomes") - pl.col("expenses"))
                .cum_sum()
                .over("category_id"),
                past=(pl.col("incomes") - pl.col("expenses"))
                .cum_sum()
                .shift(1)
                .fill_null(0)
                .over("category_id"),
            )
            .with_columns(delta=pl.col("balance") - pl.col("have"))
            .with_columns([pl.col(col).fill_null(0) for col in numeric_columns])
        )

    def make_table(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.pipe(self._missing_and_past_values)
            .with_columns(balance=(pl.col("incomes") - pl.col("expenses")))
            .with_columns(tmp_balance=pl.col("balance").cum_sum().over(["category_id"]))
            .with_columns(
                past=pl.col("tmp_balance").shift(n=1, fill_value=0).over("category_id")
            )
            .with_columns(
                balance=(pl.col("past") + pl.col("incomes") - pl.col("expenses"))
            )
            .with_columns(delta=(pl.col("have") - pl.col("balance")))
            .drop("tmp_balance")
            .sort(["category_id", "year"])
        )

    def _join_df(self, df: pl.LazyFrame, hv: pl.LazyFrame) -> pl.LazyFrame:
        # how = "full" because if df is empty, but hv is not, return df will be empty
        return df.join(
            hv,
            on=["category_id", "year"],
            how="full",
            coalesce=True,
            nulls_equal=True,
        )


class Savings(SignalBase):
    signal_type = "savings"

    def __init__(self, data: GetData):
        _in = self._make_df(data.incomes)
        _ex = self._make_df(data.expenses)
        _hv = self._make_have(data.have)
        _df = self._join_df(_in, _ex, _hv)

        self._types = data.types

        try:
            self._table = self.make_table(_df)
        except TypeError:
            self._table = _df

    def _fill_missing_past_future_rows(self, df: pl.LazyFrame) -> pl.LazyFrame:
        # Define columns to fill
        numeric_columns = [
            col
            for col in df.collect_schema().names()
            if col not in ("latest_check", "market_value")
        ]

        return (
            df.pipe(self._create_year_grid)
            .with_columns(
                # Fill numeric columns with 0
                *[pl.col(col).fill_null(0) for col in numeric_columns],
                # Forward fill market_value and latest_check
                pl.col("market_value")
                .fill_null(strategy="forward")
                .over("category_id"),
                pl.col("latest_check")
                .fill_null(strategy="forward")
                .over("category_id"),
            )
            .with_columns(
                pl.col("market_value").fill_null(0)
            )
        )

    def make_table(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.pipe(self._fill_missing_past_future_rows)
            .with_columns(
                per_year_incomes=pl.col("incomes"),
                per_year_fee=pl.col("fee"),
                past_amount=pl.col("incomes")
                .cum_sum()
                .shift(1, fill_value=0)
                .over("category_id"),
                past_fee=pl.col("fee")
                .cum_sum()
                .shift(1, fill_value=0)
                .over("category_id"),
            )
            .with_columns(
                sold=pl.col("sold").cum_sum().over("category_id"),
                sold_fee=pl.col("sold_fee").cum_sum().over("category_id"),
                incomes=(pl.col("past_amount") + pl.col("per_year_incomes")),
                fee=(pl.col("past_fee") + pl.col("per_year_fee")),
            )
            .with_columns(
                profit_sum=(pl.col("market_value") - pl.col("incomes") - pl.col("fee")),
                profit_proc=(
                    pl.when(pl.col("market_value") == 0)
                    .then(0)
                    .when(pl.col("incomes") == 0)
                    .then(0)  # Handle zero incomes to avoid division by zero
                    .otherwise(
                        ((pl.col("market_value") - pl.col("fee")) / pl.col("incomes"))
                        * 100
                        - 100
                    )
                ).round(2),
            )
            .sort(["category_id", "year"])
        )

    def _join_df(
        self, inc: pl.LazyFrame, exp: pl.LazyFrame, hv: pl.LazyFrame
    ) -> pl.LazyFrame:
        # drop expenses column
        inc = inc.drop("expenses")
        # drop incomes column, rename fee
        exp = exp.drop("incomes")
        exp = exp.rename({"fee": "sold_fee", "expenses": "sold"})

        return (
            inc.join(
                exp,
                on=["category_id", "year"],
                how="full",
                coalesce=True,
                nulls_equal=True,
            )
            .join(
                hv,
                on=["category_id", "year"],
                how="full",
                coalesce=True,
                nulls_equal=True,
            )
            .rename({"have": "market_value"})
        )
