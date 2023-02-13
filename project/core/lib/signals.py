import contextlib
import itertools as it
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import polars as pl
from polars import DataFrame as DF


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
        self.have = self._get_data(self.conf.get("have"), "have")
        self.types = self._get_data(self.conf.get("types"), "related")

    def _get_data(self, models: tuple, method: str):
        items = []

        if not models:
            return items

        for model in models:
            with contextlib.suppress(AttributeError):
                _method = getattr(model.objects, method)
                if _qs := _method():
                    items.extend(list(_qs))
        return items


class SignalBase(ABC):
    signal_type = None

    @property
    def types(self) -> dict:
        return {category.id: category for category in self._types}

    @property
    def table(self):
        return self._table.to_dicts()

    @abstractmethod
    def make_table(self, df: DF) -> DF:
        ...

    def _make_df(self, arr: list[dict]) -> DF:
        schema = {
            "id": pl.UInt16,
            "year": pl.UInt16,
            "incomes": pl.Float64,
            "expenses": pl.Float64,
        }
        if self.signal_type == "savings":
            schema |= {"fee": pl.Float64}

        df = pl.DataFrame(arr, schema=schema)
        if df.is_empty():
            return df

        return (
            df.with_columns(
                [pl.col("incomes").fill_null(0.0), pl.col("expenses").fill_null(0.0)]
            )
            .groupby(["id", "year"])
            .agg(pl.all().sum())
            .sort(["year", "id"])
        )

    def _make_have(self, have: list[dict]) -> DF:
        schema = {
            "id": pl.UInt16,
            "year": pl.UInt16,
            "have": pl.Float64,
            "latest_check": pl.Datetime,
        }
        df = pl.DataFrame(have, schema=schema)

        df = df.sort(["year", "id"])
        return df

    def _get_past_records(self, df: DF) -> pl.Expr:
        years = df.select(pl.col("year").unique().sort())["year"]
        if len(years) < 2:
            return df

        prev_year = years[-2]
        last_year = years[-1]

        types = [x.pk for x in self._types]

        row_diff = (
            df.filter(pl.col("year").is_in([prev_year, last_year]))
            .select([pl.all()])
            .groupby(["year"])
            .agg([pl.col("id").alias("tmp")])
        )
        prev_year_type_list = row_diff[0, 1]
        last_year_type_list = row_diff[1, 1]
        row_diff = list(set(prev_year_type_list) ^ set(last_year_type_list))

        df = df.vstack(
            df.filter(
                (pl.col("year") == prev_year)
                & (pl.col("id").is_in(types))
                & (pl.col("id").is_in(row_diff))
            )
            .with_columns(year=pl.lit(last_year).cast(pl.UInt16))
            .pipe(self._reset_values, year=last_year)
        )
        return df

    def _insert_missing_values(self, df: DF, field_name: str) -> DF:
        df = (
            df.pipe(self._get_past_records)
            .sort(["id", "year"])
            .pipe(self._copy_cell_from_previous_year, field_name=field_name)
            .sort(["year", "id"])
            .pipe(self._insert_future_data)
        )
        return df

    def _copy_cell_from_previous_year(self, df: DF, field_name: str) -> pl.Expr:
        return df.with_columns(
            pl.col("latest_check").forward_fill(),
            pl.col(field_name).forward_fill(),
        ).with_columns(pl.col(field_name).fill_null(0.0))

    def _insert_future_data(self, df: DF) -> DF:
        """copy last year values into future (year + 1)"""
        last_year = df["year"][-1]

        df = pl.concat(
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
        return df

    def _reset_values(self, df: DF, year: int) -> pl.Expr:
        if self.signal_type == "savings":
            df = df.filter(pl.col("year") == year).with_columns(
                incomes=pl.lit(0.0),
                fee=pl.lit(0.0),
                sold=pl.lit(0.0),
                sold_fee=pl.lit(0.0),
            )

        if self.signal_type == "accounts":
            df = df.filter(pl.col("year") == year).with_columns(
                incomes=pl.lit(0.0), expenses=pl.lit(0.0)
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

    def make_table(self, df: DF) -> DF:
        if df.is_empty():
            return df

        df = (
            df.pipe(self._insert_missing_values, field_name="have")
            .with_columns(balance=pl.lit(0.0), past=pl.lit(0.0), delta=pl.lit(0.0))
            .sort(["id", "year"])
            .with_columns(balance=(pl.col("incomes") - pl.col("expenses")))
            .with_columns(tmp_balance=pl.col("balance").cumsum().over(["id"]))
            .with_columns(
                past=pl.col("tmp_balance")
                .shift_and_fill(periods=1, fill_value=0.0)
                .over("id")
            )
            .with_columns(
                balance=(pl.col("past") + pl.col("incomes") - pl.col("expenses"))
            )
            .with_columns(delta=(pl.col("have") - pl.col("balance")))
            .drop("tmp_balance")
        )
        return df

    def _join_df(self, df: DF, hv: DF) -> DF:
        df = (
            df.join(hv, on=["id", "year"], how="outer")
            .with_columns(
                [pl.col("incomes").fill_null(0.0), pl.col("expenses").fill_null(0.0)]
            )
            .sort(["year", "id"])
        )
        return df


class Savings(SignalBase):
    signal_type = "savings"

    def __init__(self, data: GetData):
        _in = self._make_df(data.incomes)
        _ex = self._make_df(data.expenses)
        _hv = self._make_have(data.have)
        _df = self._join_df(_in, _ex, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: DF) -> DF:
        if df.is_empty():
            return df

        df = (
            df.pipe(self._insert_missing_values, field_name="market_value")
            .sort(["id", "year"])
            .with_columns(
                per_year_incomes=pl.col("incomes"), per_year_fee=pl.col("fee")
            )
            .pipe(self._calc_past)
            .with_columns(
                sold=pl.col("sold").cumsum().over("id"),
                sold_fee=pl.col("sold_fee").cumsum().over("id"),
            )
            .with_columns(
                incomes=(pl.col("past_amount") + pl.col("per_year_incomes")),
                fee=(pl.col("past_fee") + pl.col("per_year_fee")),
            )
            .with_columns(
                invested=(
                    pl.lit(0.0)
                    + pl.col("incomes")
                    - pl.col("fee")
                    - pl.col("sold")
                    - pl.col("sold_fee")
                )
            )
            .with_columns(
                invested=(
                    pl.when(pl.col("invested") < 0)
                    .then(0.0)
                    .otherwise(pl.col("invested"))
                )
            )
            .with_columns(profit_sum=(pl.col("market_value") - pl.col("invested")))
            .pipe(self._calc_percent)
        )
        return df

    def _calc_past(self, df: DF) -> pl.Expr:
        df = (
            df.with_columns(tmp=pl.col("per_year_incomes").cumsum().over("id"))
            .with_columns(
                past_amount=pl.col("tmp")
                .shift_and_fill(periods=1, fill_value=0.0)
                .over("id")
            )
            .with_columns(tmp=pl.col("per_year_fee").cumsum().over("id"))
            .with_columns(
                past_fee=pl.col("tmp")
                .shift_and_fill(periods=1, fill_value=0.0)
                .over("id")
            )
            .drop("tmp")
        )
        return df

    def _join_df(self, inc: DF, exp: DF, hv: DF) -> DF:
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
            "invested",
            "profit_proc",
            "profit_sum",
        ]

        return (
            inc.join(exp, on=["id", "year"], how="outer")
            .join(hv, on=["id", "year"], how="outer")
            .rename({"have": "market_value"})
            .with_columns(
                pl
                .exclude(["id", "year", "latest_check", "market_value"])
                .fill_null(0.0)
            )
            .with_columns([pl.lit(0.0).alias(col) for col in cols])
        )

    @staticmethod
    def calc_percent(market, invested):
        try:
            return ((market * 100) / invested) - 100
        except ZeroDivisionError:
            return 0.0

    def _calc_percent(self, df):
        df = df.with_columns(
            profit_proc=Savings.calc_percent(
                pl.col("market_value"), pl.col("invested")
            ).fill_nan(0.0)
        ).with_columns(
            profit_proc=pl.when(pl.col("profit_proc").is_infinite())
            .then(0.0)
            .otherwise(pl.col("profit_proc"))
        )
        return df
