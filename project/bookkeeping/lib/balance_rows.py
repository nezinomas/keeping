import polars as pl

from ...core.lib.signals import GetData, SignalBase


class Accounts(SignalBase):
    def __init__(self, data: GetData):
        _df = self._make_df([*data.incomes, *data.expenses])
        _hv = self._make_have(data.have)
        _df = self._join_df(_df, _hv)

        self._types = data.types

        self._table = self._build_table(data, _df)

    def _fill_missing_past_future_rows(self, df: pl.LazyFrame) -> pl.LazyFrame:
        numeric_columns = [
            col for col, _ in df.collect_schema().items() if col != "latest_check"
        ]

        return (
            df.pipe(self._create_year_grid)
            .with_columns(
                pl.col("have", "latest_check")
                .fill_null(strategy="forward")
                .over("category_id"),
            )
            .with_columns([pl.col(col).fill_null(0) for col in numeric_columns])
        )

    def make_table(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.pipe(self._fill_missing_past_future_rows)
            .with_columns(
                past=(pl.col("incomes") - pl.col("expenses"))
                .cum_sum()
                .shift(n=1, fill_value=0)
                .over("category_id")
            )
            .with_columns(
                balance=(pl.col("past") + pl.col("incomes") - pl.col("expenses"))
            )
            .with_columns(delta=(pl.col("have") - pl.col("balance")))
            .sort(["category_id", "year"])
        )

    def _join_df(self, df: pl.LazyFrame, hv: pl.LazyFrame) -> pl.LazyFrame:
        # a full join keeps a worth whose year has no incomes or expenses
        return df.join(
            hv,
            on=["category_id", "year"],
            how="full",
            coalesce=True,
            nulls_equal=True,
        )


class Savings(SignalBase):
    @property
    def schema(self) -> dict:
        return super().schema | {"fee": pl.Int32}

    def __init__(self, data: GetData):
        _in = self._make_df(data.incomes)
        _ex = self._make_df(data.expenses)
        _hv = self._make_have(data.have)
        _df = self._join_df(_in, _ex, _hv)

        self._types = data.types
        self._moves = self._make_moves(data.moves)

        self._table = self._build_table(data, _df)

    def _fill_missing_past_future_rows(self, df: pl.LazyFrame) -> pl.LazyFrame:
        numeric_columns = [
            col
            for col in df.collect_schema().names()
            if col not in ("latest_check", "market_value")
        ]

        return (
            df.pipe(self._create_year_grid)
            .with_columns(
                *[pl.col(col).fill_null(0) for col in numeric_columns],
                pl.col("market_value")
                .fill_null(strategy="forward")
                .over("category_id"),
                pl.col("latest_check")
                .fill_null(strategy="forward")
                .over("category_id"),
            )
            .with_columns(pl.col("market_value").fill_null(0))
        )

    def make_table(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.pipe(self._fill_missing_past_future_rows)
            .pipe(self._add_sold_since_check)
            .pipe(self._zero_worth_in_close_year_after_a_sell)
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
                profit_sum=(
                    pl.col("market_value")
                    + pl.col("sold")
                    - pl.col("incomes")
                    - pl.col("fee")
                )
            )
            .with_columns(
                profit_proc=(
                    pl.when(
                        (pl.col("incomes") == 0)
                        | ((pl.col("market_value") == 0) & (pl.col("sold") == 0))
                    )
                    .then(0)
                    .otherwise(pl.col("profit_sum") / pl.col("incomes") * 100)
                ).round(2),
            )
            .sort(["category_id", "year"])
        )

    def _add_sold_since_check(self, df: pl.LazyFrame) -> pl.LazyFrame:
        # a move carries only a date, so one on the worth's own day counts as after it
        stale = (
            df.select("category_id", "year", "latest_check")
            .join(self._moves, on="category_id", suffix="_move")
            .filter(
                (pl.col("year_move") <= pl.col("year"))
                & (pl.col("date") >= pl.col("latest_check").dt.date())
            )
            .group_by("category_id", "year")
            .agg(sold_since_check=pl.col("price").sum())
        )
        return df.join(
            stale, on=["category_id", "year"], how="left", maintain_order="left"
        ).with_columns(pl.col("sold_since_check").fill_null(0).cast(pl.Int32))

    def _zero_worth_in_close_year_after_a_sell(self, df: pl.LazyFrame) -> pl.LazyFrame:
        # a worth after a sell is money already counted in sold; sold is still
        # the year's own here, so the running total is taken for this check only
        sold_in_close_year = (pl.col("year") == pl.col("closed")) & (
            pl.col("sold").cum_sum().over("category_id", order_by="year") > 0
        )
        return (
            df.join(
                self._closed_years(),
                on="category_id",
                how="left",
                maintain_order="left",
            )
            .with_columns(
                market_value=pl.when(sold_in_close_year)
                .then(0)
                .otherwise(pl.col("market_value")),
                sold_since_check=pl.when(sold_in_close_year)
                .then(0)
                .otherwise(pl.col("sold_since_check")),
            )
            .drop("closed")
        )

    def _join_df(
        self, inc: pl.LazyFrame, exp: pl.LazyFrame, hv: pl.LazyFrame
    ) -> pl.LazyFrame:
        inc = inc.drop("expenses")
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
