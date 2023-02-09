import contextlib
import itertools as it
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd
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
    @property
    def types(self) -> dict:
        return {category.id: category for category in self._types}

    @property
    def table(self):
        return self._table.to_dicts()

    @abstractmethod
    def make_table(self, df: DF) -> DF:
        ...

    def _make_df(self, arr: list[dict], cols: list) -> DF:
        # create df from incomes and expenses
        df = pl.DataFrame(arr)
        if df.is_empty():
            return df

        df = (
            df.fill_null(0.0)
            .with_columns(
                [pl.col("year").cast(pl.UInt16), pl.col("id").cast(pl.UInt16)]
            )
            .groupby(["id", "year"])
            .agg(pl.all().sum())
            .sort(["year", "id"])
        )
        return df

    def _make_have(self, have: list[dict]) -> DF:
        df = pl.DataFrame(have)
        df = df.with_columns(
            [pl.col("year").cast(pl.UInt16), pl.col("id").cast(pl.UInt16)]
        ).sort(["year", "id"])
        return df

    def _get_past_records(self, df: DF, prev_year: int, last_year: int) -> pl.Expr:
        types = [x.pk for x in self._types]
        row_diff = (
            df.filter(pl.col("year").is_in([prev_year, last_year]))
            .select([pl.all()])
            .groupby(["year"])
            .agg([pl.col("id").alias("tmp")])
            .with_columns(pl.col("tmp"))
        )
        row_diff = list(set(row_diff[0, 1]) - set(row_diff[1, 1]))

        df = (
            df.filter(
                (pl.col("year") == prev_year)
                & (pl.col("id").is_in(types))
                & (pl.col("id").is_in(row_diff))
            )
            .with_columns(pl.lit(last_year).cast(pl.UInt16).alias("year"))
            .pipe(self._reset_values, year=last_year)
        )
        return df

    def _insert_missing_values(self, df: DF, field_name: str) -> DF:
        years = df.select(pl.col("year").unique().sort())["year"].to_list()
        prev_year = years[-2]
        last_year = years[-1]

        df = (
            df.vstack(
                df.pipe(
                    self._get_past_records, prev_year=prev_year, last_year=last_year
                )
            )
            .sort(["id", "year"])
            .with_columns(
                [
                    pl.col("latest_check").forward_fill(),
                    pl.col("have").forward_fill(),
                ]
            )
            .with_columns(pl.col("have").fill_null(0.0))
            .sort(["year", "id"])
            .pipe(self._insert_future_data, last_year=last_year)
        )
        return df

    def _insert_future_data(self, df: DF, last_year) -> DF:
        """copy last year values into future (year + 1)"""
        df = pl.concat(
            [
                df,
                (
                    df.filter(pl.col("year") == df["year"][-1])
                    .with_columns(pl.lit(last_year + 1).cast(pl.UInt16).alias("year"))
                    .pipe(self._reset_values, year=(last_year + 1))
                ),
            ],
            how="vertical",
        )
        return df

    def _reset_values(self, df: DF, year: int) -> pl.Expr:
        if "fee" in df.columns:
            df = df.filter(pl.col("year") == year).with_columns(
                [
                    pl.lit(0.0).alias("incomes"),
                    pl.lit(0.0).alias("fee"),
                    pl.lit(0.0).alias("sold"),
                    pl.lit(0.0).alias("sold_fee"),
                ]
            )
        else:
            df = df.filter(pl.col("year") == year).with_columns(
                [
                    pl.lit(0.0).alias("incomes"),
                    pl.lit(0.0).alias("expenses"),
                ]
            )
        return df


class Accounts(SignalBase):
    def __init__(self, data: GetData):
        cols = ["incomes", "expenses"]
        _df = self._make_df(it.chain(data.incomes, data.expenses), cols)
        _hv = self._make_have(data.have)
        _df = self._join_df(_df, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: DF) -> DF:
        if df.is_empty():
            return df

        def _missing_cols(df) -> pl.Expr:
            cols = ["incomes", "expenses"]
            diff = [col_name for col_name in cols if col_name not in df.columns]
            return df.with_columns([pl.lit(0.0).alias(col_name) for col_name in diff])

        print(f"------------------------------->make_table IN\n{df}\n")
        df = (
            df.pipe(_missing_cols)
            .pipe(self._insert_missing_values, field_name="have")
            .with_columns(
                [
                    pl.lit(0.0).alias("balance"),
                    pl.lit(0.0).alias("past"),
                    pl.lit(0.0).alias("delta"),
                ]
            )
            .sort(["id", "year"])
            .with_columns((pl.col("incomes") - pl.col("expenses")).alias("balance"))
            .with_columns(pl.col("balance").cumsum().over(["id"]).alias("tmp_balance"))
            .with_columns(
                pl.col("tmp_balance")
                .shift_and_fill(periods=1, fill_value=0.0)
                .over("id")
                .alias("past")
            )
            .with_columns(
                (pl.col("past") + pl.col("incomes") - pl.col("expenses")).alias(
                    "balance"
                )
            )
            .with_columns((pl.col("have") - pl.col("balance")).alias("delta"))
            .drop("tmp_balance")
        )
        # df.balance = df.incomes - df.expenses
        # # temp column for each id group with balance cumulative sum
        # df['temp'] = df.groupby("id")['balance'].cumsum()
        # # calculate past -> shift down temp column
        # df['past'] = df.groupby("id")['temp'].shift(fill_value=0.0)
        # # recalculate balance with past and drop temp
        # df['balance'] = df['past'] + df['incomes'] - df['expenses']
        # df.drop(columns=["temp"], inplace=True)
        # # calculate delta between have and balance
        # df.delta = df.have - df.balance
        # print(f'------------------------------->make_table OUT\n{df.select(pl.exclude(["latest_check"]))}\n')
        print(
            f'------------------------------->make_table OUT\n{df.select(pl.exclude(["expenses",]))}\n'
        )
        return df

    def _join_df(self, df: DF, hv: DF) -> DF:
        df = (
            df.join(hv, on=["id", "year"], how="outer")
            .with_columns(pl.col("have"))
            .sort(["year", "id"])
        )
        return df


class Savings(SignalBase):
    def __init__(self, data: GetData):
        cols = ["incomes", "expenses", "fee"]
        _in = self._make_df(data.incomes, cols)
        _ex = self._make_df(data.expenses, cols)
        _hv = self._make_have(data.have)
        _df = self._join_df(_in, _ex, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: DF) -> DF:
        if df.empty:
            return df
        df = self._insert_missing_values(df, "market_value")
        # calculate incomes
        df.per_year_incomes = df.incomes
        df.per_year_fee = df.fee
        # past_amount and past_fee
        df = self._calc_past(df)
        # calculate sold
        df.sold = df.groupby("id")["sold"].cumsum()
        df.sold_fee = df.groupby("id")["sold_fee"].cumsum()
        # recalculate incomes and fees with past values
        df.incomes = df.past_amount + df.per_year_incomes
        df.fee = df.past_fee + df.per_year_fee
        # calculate invested, invested cannot by negative
        df.invested = df.incomes - df.fee - df.sold - df.sold_fee
        df.invested = df.invested.mask(df.invested < 0, 0.0)
        # calculate profit/loss
        df.profit_sum = df.market_value - df.invested
        df.profit_proc = df[["market_value", "invested"]].apply(
            Savings.calc_percent, axis=1
        )
        return df

    def _calc_past(self, df: DF) -> DF:
        df["tmp"] = df.groupby("id")["per_year_incomes"].cumsum()
        df.past_amount = df.groupby("id")["tmp"].shift(fill_value=0.0)
        # calculate past_fee
        df["tmp"] = df.groupby("id")["per_year_fee"].cumsum()
        df.past_fee = df.groupby("id")["tmp"].shift(fill_value=0.0)
        # drop tmp columns
        df.drop(columns=["tmp"], inplace=True)
        return df

    def _join_df(self, inc: DF, exp: DF, hv: DF) -> DF:
        # drop expenses column
        inc.drop(columns=["expenses"], inplace=True)
        # drop incomes column, rename fee
        exp.drop(columns=["incomes"], inplace=True)
        exp.rename(columns={"fee": "sold_fee", "expenses": "sold"}, inplace=True)
        # concat dataframes, sum fees
        df = pd.concat([inc, exp, hv], axis=1).fillna(0.0)
        # rename have -> market_value
        df.rename(columns={"have": "market_value"}, inplace=True)
        # create columns
        cols = [
            "past_amount",
            "past_fee",
            "per_year_incomes",
            "per_year_fee",
            "invested",
            "profit_proc",
            "profit_sum",
        ]
        df[cols] = 0.0

        return df

    @staticmethod
    def calc_percent(args):
        market = args[0]
        invested = args[1]

        rtn = 0.0
        if invested:
            rtn = ((market * 100) / invested) - 100

        return rtn
