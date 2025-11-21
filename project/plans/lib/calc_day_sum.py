import contextlib
import itertools as it
from collections import namedtuple
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast

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
    def __init__(self, data: PlanCollectData, month: int = 0):
        self._data: PlanCollectData = data
        self.month: int = month

        self.df: pl.DataFrame = pl.DataFrame()
        self.calculated: bool = False

    def __getattr__(self, name: str) -> int | dict:
        """
        Dynamically provide access to calculated plan rows.

        Attributes like ``incomes_avg``, ``day_calced``, ``expenses_necessary``, etc.
        are not stored as individual instance attributes. Instead, when first accessed
        they are resolved from the internal DataFrame that is built lazily in ``_calc_df()``.

        The mapping is driven by the ``Row`` StrEnum: the attribute name is upper-cased
        and used to look up the corresponding enum member. This keeps the public API
        concise and DRY while guaranteeing a one-to-one relationship with the enum
        that is the single source of truth for row identifiers.

        If the name does not match any ``Row`` member, a standard ``AttributeError``
        is raised so that typos are caught early and IDE tooling remains accurate.
        """
        try:
            return self._get_row(Row[name.upper()])
        except KeyError as exc:
            raise AttributeError(
                f"{self.__class__.__name__} has no attribute '{name}'"
            ) from exc

    @property
    def plans_stats(self):
        Items = namedtuple("Items", ["type", *MONTH_NAMES])

        return [
            Items(
                type=f"1. {_('Incomes')} ({_('median')})",
                **cast(dict, self.incomes_avg),
            ),
            Items(
                type=f"2. {_('Necessary expenses')}",
                **cast(dict, self.expenses_necessary),
            ),
            Items(
                type=f"3. {_('Remains for everyday')} (1 - 2)",
                **cast(dict, self.expenses_free),
            ),
            Items(
                type=f"4. {_('Remains for everyday')} ({_('from tables above')})",
                **cast(dict, self.expenses_free2),
            ),
            Items(
                type=f"5. {_('Full expenses')} (1 + 4)",
                **cast(dict, self.expenses_full),
            ),
            Items(
                type=f"6. {_('Incomes')} - {_('Full expenses')} (1 - 5)",
                **cast(dict, self.expenses_remains),
            ),
            Items(
                type=f"7. {_('Sum per day')} (3 / {_('days in month')})",
                **cast(dict, self.day_calced),
            ),
            Items(
                type=f"8. {_('Residual')} (3 - 7 * {_('days in month')})",
                **cast(dict, self.remains),
            ),
        ]

    @property
    def monthly_plan_by_category(self) -> dict:
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

    def _get_row(self, name: Row) -> int | dict:
        if not self.calculated and self.df.is_empty():
            self.df = self._calc_df()
            self.calculated = True

        if self.df.is_empty() or name not in self.df["name"]:
            return {}

        data = self.df.filter(pl.col("name") == name)

        return self._return_data(data)

    def _return_data(self, data: pl.DataFrame) -> int | dict:
        """
        Convert a filtered Polars DataFrame row into the appropriate return format.

        Behaviour depends on whether a specific ``month`` was requested during
        instantiation of the class:

        - If ``self.month`` is set (e.g. ``month=1`` for January):
        Returns a single ``int`` – the value for the selected month.

        - If ``self.month`` is ``None``:
        Returns a ``dict`` mapping month names to their values:
        ``{"january": 1500, "february": 1600, ..., "december": 1400}``.
        """
        select = monthname(self.month) if self.month else MONTH_NAMES
        data = data.select(select)
        return data.item() if self.month else data.to_dicts()[0]

    def _create_data(self):
        expenses_necessary, expenses_free2 = [], []

        for row in self._data.expenses:
            if row.get("necessary"):
                expenses_necessary.append({"name": Row.EXPENSES_NECESSARY, **row})
            else:
                expenses_free2.append({"name": Row.EXPENSES_FREE2, **row})

        return list(
            it.chain(
                [{"name": Row.INCOMES, **d} for d in self._data.incomes],
                [{"name": Row.SAVINGS, **d} for d in self._data.savings],
                [{"name": Row.DAY_INPUT, **d} for d in self._data.days],
                [{"name": Row.NECESSARY, **d} for d in self._data.necessary],
                [{"name": Row.MONTH_LEN, **self._data.month_len}],
                expenses_necessary,
                expenses_free2,
            )
        )

    def _create_df(self) -> pl.DataFrame:
        data = self._create_data()

        df = pl.DataFrame(data)

        df = self._insert_missing_rows(df)

        with contextlib.suppress(pl.exceptions.ColumnNotFoundError):
            df = df.group_by("name").agg(pl.col(pl.Int64).sum()).sort("name")
        return df.transpose(column_names="name")

    def _insert_missing_rows(self, df: pl.DataFrame) -> pl.DataFrame:
        required_rows = {
            Row.INCOMES,
            Row.SAVINGS,
            Row.DAY_INPUT,
            Row.NECESSARY,
            Row.EXPENSES_NECESSARY,
            Row.EXPENSES_FREE2,
        }
        current_rows = set(df["name"].to_list())

        empty_row = df.clear(1)

        for row_name in required_rows - current_rows:
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
