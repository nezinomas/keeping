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
    def df(self):
        return self._table

    @abstractmethod
    def make_table(self, df: pl.DataFrame) -> pl.DataFrame: ...

    def _make_df(self, arr: list[dict]) -> pl.DataFrame:
        schema = {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "incomes": pl.Int32,
            "expenses": pl.Int32,
        }

        if self.signal_type == "savings":
            schema |= {"fee": pl.Int32}

        if not arr:
            return pl.DataFrame(arr, schema=schema)

        df = pl.from_dicts(arr, schema=schema)

        return (
            df.with_columns(
                [pl.col("incomes").fill_null(0), pl.col("expenses").fill_null(0)]
            )
            .group_by(["category_id", "year"])
            .agg(pl.all().sum())
        )

    def _make_have(self, have: list[dict]) -> pl.DataFrame:
        schema = {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "have": pl.UInt32,
            "latest_check": pl.Datetime,
        }
        return pl.DataFrame(have, schema=schema)

    def _create_year_grid(self, df: pl.LazyFrame) -> pl.Expr:
        # Get global max_year
        global_max_year = df.select(pl.col("year").max()).collect().item()
        global_min_year = df.select(pl.col("year").min()).collect().item()

        # Get min_year per category_id
        min_year_ranges = df.group_by("category_id").agg(min_year=pl.col("year").min())

        # Create a LazyFrame of all years from 0 to global_max_year + 1
        all_years_df = pl.LazyFrame(
            {"year": range(global_min_year, global_max_year + 2)}
        )

        # Create all combinations of category_id and years, filtering by min_year
        all_years = (
            min_year_ranges.join(all_years_df, how="cross")
            .filter(pl.col("year") >= pl.col("min_year"))
            .select(["category_id", "year"])
        )

        # Join with original DataFrame to include missing years
        df = all_years.join(df, on=["category_id", "year"], how="left")

        #  list of categories with closed years
        closed = pl.from_dicts(
            [{"category_id": x.pk, "closed": x.closed} for x in self._types]
        ).lazy()

        return (
            df.join(closed, on="category_id", how="inner")
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
        _df = self._join_df(_df.lazy(), _hv.lazy())

        self._types = data.types

        try:
            self._table = self.make_table(_df).collect()
        except TypeError:
            self._table = _df.collect()

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
        _df = self._join_df(_in.lazy(), _ex.lazy(), _hv.lazy())

        self._types = data.types

        try:
            self._table = self.make_table(_df).collect()
        except TypeError:
            self._table = _df.collect()

    def _fill_missing_past_future_rows(self, df: pl.LazyFrame) -> pl.LazyFrame:
        # Define columns to fill
        numeric_columns = [
            col
            for col, _ in df.collect_schema().items()
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
                # Fill remaining market_value nulls with 0
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
        # additional columns
        cols = [
            "past_amount",
            "past_fee",
            "per_year_incomes",
            "per_year_fee",
            "profit_sum",
        ]

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
            .lazy()
            .rename({"have": "market_value"})
            .with_columns(
                pl.exclude(
                    ["category_id", "year", "latest_check", "market_value"]
                ).fill_null(0)
            )
            .with_columns([pl.lit(0).alias(col) for col in cols])
        )
