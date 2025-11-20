import contextlib
import itertools as it
from collections import namedtuple
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property

import polars as pl
from django.db.models import F
from django.utils.translation import gettext as _

from ...core.lib.date import MOTHS_WITH_DAYS_GENERIC, monthlen, monthname, monthnames
from ...users.models import User
from ..models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan
from ..services.model_services import ModelService

MONTH_NAMES = monthnames()


class Row(StrEnum):
    """All possible row names in the calculation dataframe."""

    INCOMES = "incomes"
    SAVINGS = "savings"
    DAY_INPUT = "day_input"
    NECESSARY = "necessary"
    MONTH_LEN = "month_len"

    # Calculated / derived rows
    INCOMES_AVG = "incomes_avg"
    EXPENSES_NECESSARY = "expenses_necessary"
    EXPENSES_FREE = "expenses_free"
    EXPENSES_FREE2 = "expenses_free2"
    EXPENSES_FULL = "expenses_full"
    EXPENSES_REMAINS = "expenses_remains"
    DAY_CALCED = "day_calced"
    REMAINS = "remains"


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

    @cached_property
    def incomes(self) -> dict | float:
        return self._get_row(Row.INCOMES)

    @cached_property
    def incomes_avg(self) -> dict | float:
        return self._get_row(Row.INCOMES_AVG)

    @cached_property
    def savings(self) -> dict | float:
        return self._get_row(Row.SAVINGS)

    @cached_property
    def expenses_necessary(self) -> dict | float:
        return self._get_row(Row.EXPENSES_NECESSARY)

    @cached_property
    def expenses_free(self) -> dict | float:
        return self._get_row(Row.EXPENSES_FREE)

    @cached_property
    def expenses_free2(self) -> dict | float:
        return self._get_row(Row.EXPENSES_FREE2)

    @cached_property
    def expenses_full(self) -> dict | float:
        return self._get_row(Row.EXPENSES_FULL)

    @cached_property
    def expenses_remains(self) -> dict | float:
        return self._get_row(Row.EXPENSES_REMAINS)

    @cached_property
    def day_calced(self) -> dict | float:
        return self._get_row(Row.DAY_CALCED)

    @cached_property
    def day_input(self) -> dict | float:
        return self._get_row(Row.DAY_INPUT)

    @cached_property
    def remains(self) -> dict | float:
        return self._get_row(Row.REMAINS)

    @property
    def plans_stats(self):
        Items = namedtuple("Items", ["type", *MONTH_NAMES])

        return [
            Items(type=f"1. {_('Incomes')} ({_('median')})", **self.incomes_avg),
            Items(type=f"2. {_('Necessary expenses')}", **self.expenses_necessary),
            Items(type=f"3. {_('Remains for everyday')} (1 - 2)", **self.expenses_free),
            Items(
                type=f"4. {_('Remains for everyday')} ({_('from tables above')})",
                **self.expenses_free2,
            ),
            Items(type=f"5. {_('Full expenses')} (1 + 4)", **self.expenses_full),
            Items(
                type=f"6. {_('Incomes')} - {_('Full expenses')} (1 - 5)",
                **self.expenses_remains,
            ),
            Items(
                type=f"7. {_('Sum per day')} (3 / {_('days in month')})",
                **self.day_calced,
            ),
            Items(
                type=f"8. {_('Residual')} (3 - 7 * {_('days in month')})",
                **self.remains,
            ),
        ]

    @property
    def monthly_plan_by_category(self) -> dict:
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
            .select(["title", month])
            .group_by("title")
            .agg(pl.col(month).sum())
            .sort("title")
        )
        return dict(zip(df["title"], df[month]))

    def _get_row(self, name: str) -> dict | float:
        if not self.calculated and self.df.is_empty():
            self.df = self._calc_df()
            self.calculated = True

        if self.df.is_empty() or name not in self.df["name"]:
            return {}

        data = self.df.filter(pl.col("name") == name)

        return self._return_data(data)

    def _return_data(self, data: pl.DataFrame) -> float | dict:
        """If data is polars Serries convert data to dictionary"""
        select = monthname(self.month) if self.month else MONTH_NAMES
        data = data.select(select)
        return data.item() if self.month else data.to_dicts()[0]

    def _create_df(self) -> pl.DataFrame:
        data = list(
            it.chain(
                [{"name": Row.INCOMES, **d} for d in self._data.incomes],
                [{"name": "expenses", **d} for d in self._data.expenses],
                [{"name": Row.SAVINGS, **d} for d in self._data.savings],
                [{"name": Row.DAY_INPUT, **d} for d in self._data.days],
                [{"name": Row.NECESSARY, **d} for d in self._data.necessary],
                [{"name": Row.MONTH_LEN, **self._data.month_len}],
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
                    .then(pl.lit(Row.EXPENSES_NECESSARY))
                    .otherwise(pl.lit(Row.EXPENSES_FREE2))
                    .alias("name")
                )
                .group_by("name")
                .agg(pl.col(pl.Int64).sum())
                .sort("name")
            )
        return df.transpose(column_names="name")

    def _insert_missing_rows(self, df: pl.DataFrame) -> pl.DataFrame:
        required_rows = [
            Row.INCOMES,
            Row.SAVINGS,
            Row.DAY_INPUT,
            Row.NECESSARY,
            Row.EXPENSES_NECESSARY,
            Row.EXPENSES_FREE2,
        ]
        current_rows = set(df["name"].to_list())
        empty_row = df.clear(1)

        for row_name in required_rows:
            if row_name not in current_rows:
                df = df.vstack(
                    empty_row.with_columns(pl.lit(row_name).alias("name")).fill_null(0)
                )
        return df

    def _calc_df(self) -> pl.DataFrame:
        df = self._create_df()

        return (
            df.lazy()
            .with_columns(
                incomes_avg=pl.col(Row.INCOMES).median(),
                expenses_necessary=(
                    pl.lit(0)
                    + pl.col(Row.EXPENSES_NECESSARY)
                    + pl.col(Row.SAVINGS)
                    + pl.col(Row.NECESSARY)
                ),
            )
            .with_columns(
                expenses_free=(pl.col(Row.INCOMES_AVG) - pl.col(Row.EXPENSES_NECESSARY))
            )
            .with_columns(
                expenses_full=(
                    pl.col(Row.EXPENSES_NECESSARY) + pl.col(Row.EXPENSES_FREE2)
                )
            )
            .with_columns(
                day_calced=(pl.col(Row.EXPENSES_FREE) / pl.col(Row.MONTH_LEN))
            )
            .with_columns(
                remains=(
                    pl.col(Row.EXPENSES_FREE)
                    - (pl.col(Row.DAY_INPUT) * pl.col(Row.MONTH_LEN))
                )
            )
            .with_columns(
                expenses_remains=(pl.col(Row.INCOMES_AVG) - pl.col(Row.EXPENSES_FULL))
            )
            .collect()
            .transpose(
                include_header=True, header_name="name", column_names=MONTH_NAMES
            )
        )
