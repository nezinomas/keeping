import contextlib
import itertools as it
from collections import namedtuple
from dataclasses import dataclass, field

import polars as pl
from django.db.models import F
from django.utils.translation import gettext as _

from ...core.lib.date import MOTHS_WITH_DAYS_GENERIC, monthlen, monthname, monthnames
from ...users.models import User
from ..models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan
from ..services.model_services import ModelService

MONTH_NAMES = monthnames()


@dataclass
class PlanCollectData:
    user: User
    year: int = field(init=False, default=1974)

    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    savings: list[dict] = field(init=False, default_factory=list)
    days: list[dict] = field(init=False, default_factory=list)
    necessary: list[dict] = field(init=False, default_factory=list)
    month_len: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.year = self.user.year

        self.incomes = (
            ModelService(IncomePlan, self.user).year(self.year).values(*MONTH_NAMES)
        )

        self.expenses = (
            ModelService(ExpensePlan, self.user)
            .year(self.year)
            .values(
                *MONTH_NAMES,
                necessary=F("expense_type__necessary"),
                title=F("expense_type__title"),
            )
        )

        self.savings = (
            ModelService(SavingPlan, self.user).year(self.year).values(*MONTH_NAMES)
        )
        self.days = (
            ModelService(DayPlan, self.user).year(self.year).values(*MONTH_NAMES)
        )
        self.necessary = (
            ModelService(NecessaryPlan, self.user)
            .year(self.year)
            .values(*MONTH_NAMES)
            .annotate(title=F("expense_type__title"))
        )

        self.month_len = MOTHS_WITH_DAYS_GENERIC
        # update february value
        self.month_len["february"] = monthlen(self.year, "february")


class PlanCalculateDaySum:
    def __init__(self, data: PlanCollectData, month: int | None = None):
        self._data = data
        self.month = month

        self.df: pl.DataFrame = pl.DataFrame()
        self.calculated: bool = False

    def filter_df(self, name: str) -> dict | float:
        if not self.calculated and self.df.is_empty():
            self.df = self._calc_df()
            self.calculated = True

        if self.df.is_empty() or name not in self.df["name"]:
            return {}

        data = self.df.filter(pl.col("name") == name)

        return self._return_data(data)

    @property
    def plans_stats(self):
        Items = namedtuple("Items", ["type", *MONTH_NAMES])

        _incomes = _("Incomes")
        _median = _("median")
        _necessary = _("Necessary expenses")
        _remain = _("Remains for everyday")
        _full = _("Full expenses")
        _residual = _("Residual")
        _sum_per_day = _("Sum per day")
        _days = _("days in month")
        _from_tables = _("from tables above")

        return [
            Items(type=f"1. {_incomes} ({_median})", **self.filter_df("incomes_avg")),
            Items(type=f"2. {_necessary}", **self.filter_df("expenses_necessary")),
            Items(type=f"3. {_remain} (1 - 2)", **self.filter_df("expenses_free")),
            Items(
                type=f"4. {_remain} ({_from_tables})",
                **self.filter_df("expenses_free2"),
            ),
            Items(type=f"5. {_full} (1 + 4)", **self.filter_df("expenses_full")),
            Items(
                type=f"6. {_incomes} - {_full} (1 - 5)",
                **self.filter_df("expenses_remains"),
            ),
            Items(
                type=f"7. {_sum_per_day} (3 / {_days})", **self.filter_df("day_calced")
            ),
            Items(
                type=f"8. {_residual} (3 - 7 * {_days})", **self.filter_df("remains")
            ),
        ]

    @property
    def targets(self) -> dict:
        pl.Config(fmt_str_lengths=50)
        pl.Config(tbl_cols=-1)
        pl.Config(set_tbl_width_chars=250)
        pl.Config.set_tbl_rows(100)

        month = monthname(self.month)
        data = [*self._data.expenses, *self._data.necessary, *self._data.savings]

        if not self.month or not data:
            return {}

        df = (
            pl.DataFrame(data)
            .with_columns(pl.col("title").fill_null(_("Savings")))
            .fill_null(0)
            .group_by("title")
            .agg(pl.col(pl.Int64).sum())
            .sort("title")
        )
        return dict(zip(df["title"], df[month]))

    def _return_data(self, data: pl.DataFrame) -> float | dict:
        """If data is polars Serries convert data to dictionary"""
        select = monthname(self.month) if self.month else MONTH_NAMES
        data = data.select(select)
        return data.item() if self.month else data.to_dicts()[0]

    def _create_df(self) -> pl.DataFrame:
        data = list(
            it.chain(
                [{"name": "incomes", **d} for d in self._data.incomes],
                [{"name": "expenses", **d} for d in self._data.expenses],
                [{"name": "savings", **d} for d in self._data.savings],
                [{"name": "day_input", **d} for d in self._data.days],
                [{"name": "necessary", **d} for d in self._data.necessary],
                [{"name": "month_len", **self._data.month_len}],
            )
        )
        df = pl.DataFrame(data)

        df = self._insert_missing_rows(df)

        with contextlib.suppress(pl.exceptions.ColumnNotFoundError):
            df = (
                df.with_columns(
                    pl.when(pl.col("name") != "expenses")
                    .then(pl.col("name"))
                    .when(pl.col("necessary") == True)
                    .then(pl.lit("expenses_necessary"))
                    .otherwise(pl.lit("expenses_free2"))
                    .alias("name")
                )
                .group_by("name")
                .agg(pl.col(pl.Int64).sum())
                .sort("name")
            )

        return df.transpose(column_names="name")

    def _insert_missing_rows(self, df: pl.DataFrame) -> pl.DataFrame:
        names = [
            "incomes",
            "savings",
            "day_input",
            "necessary",
            "expenses_necessary",
            "expenses_free2",
        ]
        rows = set(df["name"].to_list())

        empty_row = df.clear(1)

        for name in names:
            if name not in rows:
                row = empty_row.with_columns(
                    name=pl.lit(name),
                ).fill_null(0)
                df = df.vstack(row)

        return df

    def _calc_df(self) -> pl.DataFrame:
        df = self._create_df()

        return (
            df.lazy()
            .with_columns(
                incomes_avg=pl.col.incomes.median(),
                expenses_necessary=(
                    pl.lit(0)
                    + pl.col("expenses_necessary")
                    + pl.col("savings")
                    + pl.col("necessary")
                ),
            )
            .with_columns(
                expenses_free=(pl.col.incomes_avg - pl.col.expenses_necessary)
            )
            .with_columns(
                expenses_full=(pl.col("expenses_necessary") + pl.col("expenses_free2"))
            )
            .with_columns(day_calced=(pl.col("expenses_free") / pl.col("month_len")))
            .with_columns(
                remains=(
                    pl.col("expenses_free")
                    - (pl.col("day_input") * pl.col("month_len"))
                )
            )
            .with_columns(expenses_remains=(pl.col.incomes_avg - pl.col.expenses_full))
            .collect()
            .transpose(
                include_header=True, header_name="name", column_names=MONTH_NAMES
            )
        )
