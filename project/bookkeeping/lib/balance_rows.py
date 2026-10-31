import polars as pl

from ...core.lib.balance_rows import KEYS, BalanceRows, BalanceSources


class AccountBalanceRows(BalanceRows):
    def _join_sources(self, sources: BalanceSources) -> pl.LazyFrame:
        entries = self._make_df([*sources.incomes, *sources.expenses])
        worth = self._make_have(sources.have)
        return self._full_join(entries, worth)

    def _make_table(self, df: pl.LazyFrame) -> pl.LazyFrame:
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
        )


def _before_this_year(column: str) -> pl.Expr:
    return pl.col(column).cum_sum().shift(1, fill_value=0).over("category_id")


class SavingBalanceRows(BalanceRows):
    @property
    def schema(self) -> dict:
        return super().schema | {"fee": pl.Int32}

    def __init__(self, sources: BalanceSources):
        # the base's __init__ builds the rows, and they read the moves
        self._moves = self._make_moves(sources.moves)
        super().__init__(sources)

    def _join_sources(self, sources: BalanceSources) -> pl.LazyFrame:
        bought = self._make_df(sources.incomes).select(
            *KEYS, per_year_incomes="incomes", per_year_fee="fee"
        )
        sold = self._make_df(sources.expenses).select(
            *KEYS, per_year_sold="expenses", per_year_sold_fee="fee"
        )
        worth = self._make_have(sources.have)
        return self._full_join(self._full_join(bought, sold), worth)

    def _make_table(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.pipe(self._fill_missing_past_future_rows)
            .rename({"have": "market_value"})
            .pipe(self._add_sold_since_check)
            .pipe(self._zero_worth_in_close_year_after_a_sell)
            .pipe(self._add_running_totals)
            .pipe(self._add_profit)
        )

    @staticmethod
    def _make_moves(moves: list[dict]) -> pl.LazyFrame:
        schema = {"category_id": pl.UInt16, "date": pl.Date, "price": pl.Int32}
        return pl.LazyFrame(moves, schema=schema).with_columns(
            year=pl.col("date").dt.year().cast(pl.UInt16)
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
        return df.join(stale, on=KEYS, how="left", maintain_order="left").with_columns(
            pl.col("sold_since_check").fill_null(0).cast(pl.Int32)
        )

    def _zero_worth_in_close_year_after_a_sell(self, df: pl.LazyFrame) -> pl.LazyFrame:
        # a worth after a sell is money already counted in sold
        sold_in_close_year = (pl.col("year") == pl.col("closed")) & (
            pl.col("per_year_sold").cum_sum().over("category_id", order_by="year") > 0
        )
        return (
            df.join(
                self._closed_years,
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

    @staticmethod
    def _add_running_totals(df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.with_columns(
                past_amount=_before_this_year("per_year_incomes"),
                past_fee=_before_this_year("per_year_fee"),
                sold=pl.col("per_year_sold").cum_sum().over("category_id"),
                sold_fee=pl.col("per_year_sold_fee").cum_sum().over("category_id"),
            )
            .with_columns(
                incomes=pl.col("past_amount") + pl.col("per_year_incomes"),
                fee=pl.col("past_fee") + pl.col("per_year_fee"),
            )
            .drop("per_year_sold", "per_year_sold_fee")
        )

    @staticmethod
    def _add_profit(df: pl.LazyFrame) -> pl.LazyFrame:
        nothing_paid_or_held = (pl.col("incomes") == 0) | (
            (pl.col("market_value") == 0) & (pl.col("sold") == 0)
        )
        return df.with_columns(
            profit_sum=(
                pl.col("market_value")
                + pl.col("sold")
                - pl.col("incomes")
                - pl.col("fee")
            )
        ).with_columns(
            profit_proc=(
                pl.when(nothing_paid_or_held)
                .then(0)
                .otherwise(pl.col("profit_sum") / pl.col("incomes") * 100)
            ).round(2),
        )
