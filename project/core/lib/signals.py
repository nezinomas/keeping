import contextlib
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
        self.incomes = list(self._get_data(self.conf.get("incomes"), "incomes"))
        self.expenses = list(self._get_data(self.conf.get("expenses"), "expenses"))
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
    def table(self):
        return self._table.to_dicts()

    @property
    def df(self):
        return self._table

    @property
    def year_category_id_set(self) -> set:
        years = self._table["year"].to_numpy()
        ids = self._table["category_id"].to_numpy()
        return {(int(year), int(id_)) for id_, year in zip(ids, years)}

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

        df = pl.DataFrame(arr, schema=schema)
        if df.is_empty():
            return df

        return (
            df.lazy()
            .with_columns(
                [pl.col("incomes").fill_null(0), pl.col("expenses").fill_null(0)]
            )
            .group_by(["category_id", "year"])
            .agg(pl.all().sum())
            .sort(["year", "category_id"])
            .collect()
        )

    def _make_have(self, have: list[dict]) -> pl.DataFrame:
        schema = {
            "category_id": pl.UInt16,
            "year": pl.UInt16,
            "have": pl.UInt32,
            "latest_check": pl.Datetime,
        }
        df = pl.DataFrame(have, schema=schema)

        return df.sort(["year", "category_id"])

    def _get_past_records(self, df: pl.DataFrame) -> pl.Expr:
        years = df.select(pl.col("year").unique().sort())["year"]
        if len(years) < 2:
            return df

        prev_year = years[-2]
        last_year = years[-1]

        types = [x.pk for x in self._types]

        row_diff = (
            df.filter(pl.col("year").is_in([prev_year, last_year]))
            .select([pl.all()])
            .group_by(["year"])
            .agg([pl.col("category_id").alias("tmp")])
        )
        prev_year_type_list = row_diff[0, 1]
        last_year_type_list = row_diff[1, 1]
        row_diff = list(set(prev_year_type_list) ^ set(last_year_type_list))

        return df.vstack(
            df.filter(
                (pl.col("year") == prev_year)
                & (pl.col("category_id").is_in(types))
                & (pl.col("category_id").is_in(row_diff))
            )
            .with_columns(year=pl.lit(last_year).cast(pl.UInt16))
            .pipe(self._reset_values, year=last_year)
        )

    def _insert_missing_values(self, df: pl.DataFrame, field_name: str) -> pl.DataFrame:
        return (
            df.pipe(self._get_past_records)
            .sort(["category_id", "year"])
            .pipe(self._copy_cell_from_previous_year, field_name=field_name)
            .sort(["year", "category_id"])
            .pipe(self._insert_future_data)
        )

    def _copy_cell_from_previous_year(
        self, df: pl.DataFrame, field_name: str
    ) -> pl.Expr:  # noqa: E501
        return df.with_columns(
            pl.col("latest_check").forward_fill().over("category_id"),
            pl.col(field_name).forward_fill().over("category_id"),
        ).with_columns(pl.col(field_name).fill_null(0))

    def _insert_future_data(self, df: pl.DataFrame) -> pl.DataFrame:
        """copy last year values into future (year + 1)"""
        last_year = df["year"][-1]

        return pl.concat(
            [
                df,
                (
                    df.filter(pl.col("year") == last_year)
                    .with_columns(year=pl.lit(last_year + 1).cast(pl.UInt16))
                    .pipe(self._reset_values, year=(last_year + 1))
                ),
            ],
            how="vertical",
        )

    def _reset_values(self, df: pl.DataFrame, year: int) -> pl.Expr:
        if self.signal_type == "savings":
            df = df.filter(pl.col("year") == year).with_columns(
                incomes=pl.lit(0),
                fee=pl.lit(0),
                sold=pl.lit(0),
                sold_fee=pl.lit(0),
            )

        if self.signal_type == "accounts":
            df = df.filter(pl.col("year") == year).with_columns(
                incomes=pl.lit(0), expenses=pl.lit(0)
            )
        return df


class Accounts(SignalBase):
    signal_type = "accounts"

    def __init__(self, data: GetData):
        _df = self._make_df(it.chain(data.incomes, data.expenses))
        _hv = self._make_have(data.have)
        _df = self._join_df(_df, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: pl.DataFrame) -> pl.DataFrame:
        if df.is_empty():
            return df

        df = (
            df.pipe(self._insert_missing_values, field_name="have")
            .lazy()
            .with_columns(balance=pl.lit(0), past=pl.lit(0), delta=pl.lit(0))
            .sort(["category_id", "year"])
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
        )
        return df.collect()

    def _join_df(self, df: pl.DataFrame, hv: pl.DataFrame) -> pl.DataFrame:
        df = (
            df.join(
                hv,
                on=["category_id", "year"],
                how="full",
                coalesce=True,
                nulls_equal=True,
            )
            .lazy()
            .with_columns(
                [pl.col("incomes").fill_null(0), pl.col("expenses").fill_null(0)]
            )
            .sort(["year", "category_id"])
        )
        return df.collect()


class Savings(SignalBase):
    signal_type = "savings"

    def __init__(self, data: GetData):
        _in = self._make_df(data.incomes)
        _ex = self._make_df(data.expenses)
        _hv = self._make_have(data.have)
        _df = self._join_df(_in, _ex, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: pl.DataFrame) -> pl.DataFrame:
        if df.is_empty():
            return df

        df = (
            df.pipe(self._insert_missing_values, field_name="market_value")
            .lazy()
            .sort(["category_id", "year"])
            .with_columns(
                per_year_incomes=pl.col("incomes"), per_year_fee=pl.col("fee")
            )
            .pipe(self._calc_past)
            .with_columns(
                sold=pl.col("sold").cum_sum().over("category_id"),
                sold_fee=pl.col("sold_fee").cum_sum().over("category_id"),
            )
            .with_columns(
                incomes=(pl.col("past_amount") + pl.col("per_year_incomes")),
                fee=(pl.col("past_fee") + pl.col("per_year_fee")),
            )
            .with_columns(
                profit_sum=(pl.col("market_value") - pl.col("incomes") - pl.col("fee"))
            )
            .with_columns(
                profit_proc=(
                    pl.when(pl.col("market_value") == 0)
                    .then(0)
                    .otherwise(
                        ((pl.col("market_value") - pl.col("fee")) / pl.col("incomes"))
                        * 100
                        - 100
                    )
                )
            )
            .with_columns(
                profit_proc=(
                    pl.when(pl.col("profit_proc").is_infinite())
                    .then(0)
                    .otherwise(pl.col("profit_proc").round(2))
                )
            )
        )
        return df.collect()

    def _calc_past(self, df: pl.DataFrame) -> pl.Expr:
        return (
            df.lazy()
            .with_columns(tmp=pl.col("per_year_incomes").cum_sum().over("category_id"))
            .with_columns(
                past_amount=pl.col("tmp").shift(n=1, fill_value=0).over("category_id")
            )
            .with_columns(tmp=pl.col("per_year_fee").cum_sum().over("category_id"))
            .with_columns(
                past_fee=pl.col("tmp").shift(n=1, fill_value=0).over("category_id")
            )
            .drop("tmp")
        )

    def _join_df(
        self, inc: pl.DataFrame, exp: pl.DataFrame, hv: pl.DataFrame
    ) -> pl.DataFrame:  # noqa: E501
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
            .collect()
        )
