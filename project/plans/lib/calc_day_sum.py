import calendar
import contextlib
import itertools as it
from dataclasses import dataclass
from enum import StrEnum

import polars as pl
from django.utils.translation import gettext as _

from ...users.models import User
from ..services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)

MONTH_NUMS = [str(i) for i in range(1, 13)]


class InputRow(StrEnum):
    """Raw data categories provided by the SQL Database."""

    INCOMES = "incomes"
    SAVINGS = "savings"
    PER_DAY = "day_input"
    EXPENSES_REGULAR = "expenses_regular"
    EXPENSES_NECESSARY = "db_expenses_necessary"
    NECESSARY = "necessary"
    MONTH_LEN = "month_len"


class CalcRow(StrEnum):
    """Metrics dynamically calculated by the Polars engine."""

    INCOMES_AVG = "incomes_avg"
    EXPENSES_NECESSARY = "expenses_necessary"
    EXPENSES_FREE = "expenses_free"
    EXPENSES_FULL = "expenses_full"
    EXPENSES_REMAINS = "expenses_remains"
    PER_DAY = "day_calced"
    REMAINS = "remains"


@dataclass(frozen=True)
class DataDto:
    incomes: list[dict]
    expenses_regular: list[dict]
    expenses_necessary: list[dict]
    savings: list[dict]
    per_day: list[dict]
    necessary: list[dict]
    month_len: list[dict]


class PlanCollectData:
    def __init__(self, user, year):
        self.user: User = user
        self.year: int = year

    def get_data(self):
        expenses_service = ExpensePlanModelService(self.user)

        return DataDto(
            incomes=IncomePlanModelService(self.user).summed_by_month(self.year),
            expenses_regular=expenses_service.summed_by_month(self.year),
            expenses_necessary=expenses_service.summed_by_month(
                self.year, necessary=True
            ),
            savings=SavingPlanModelService(self.user).summed_by_month(self.year),
            per_day=DayPlanModelService(self.user).summed_by_month(self.year),
            necessary=NecessaryPlanModelService(self.user).summed_by_month(self.year),
            month_len=self.__map_month_day_len(),
        )

    def __map_month_day_len(self):
        return [
            {"month": month, "amount": calendar.monthrange(self.year, month)[1]}
            for month in range(1, 13)
        ]


class PlanCalculateDaySum:
    def __init__(self, data: DataDto, month: int = 0):
        self._data: DataDto = data
        self._calculated: bool = False

        self.month: int = month

        self.df: pl.DataFrame = pl.DataFrame()

    def __getattr__(self, name: str) -> int | dict:
        """
        Dynamically provide access to calculated plan rows.

        Attributes like ``incomes_avg``, ``day_calced``, ``expenses_necessary``, etc.
        are not stored as individual instance attributes. Instead, when first
        accessed they are resolved from the internal DataFrame that is built
        lazily in ``_calc_df()``.

        The mapping is driven by the ``Row`` StrEnum: the attribute name is upper-cased
        and used to look up the corresponding enum member. This keeps the public API
        concise and DRY while guaranteeing a one-to-one relationship with the enum
        that is the single source of truth for row identifiers.

        If the name does not match any ``Row`` member, a standard ``AttributeError``
        is raised so that typos are caught early and IDE tooling remains accurate.
        """

        with contextlib.suppress(ValueError):
            CalcRow(name)
            return self.get_row(name)

        with contextlib.suppress(ValueError):
            InputRow(name)
            return self.get_row(name)

        raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")

    def plans_stats(self):
        # Define strings cleanly so xgettext never misses them
        _incomes = _("Incomes")
        _median = _("median")
        _necessary = _("Necessary expenses")
        _remains = _("Remains for everyday")
        _from_tables = _("from tables above")
        _full = _("Full expenses")
        _sum_per_day = _("Sum per day")
        _days_in_month = _("days in month")
        _residual = _("Residual")

        return {
            f"1. {_incomes} ({_median})": self.incomes_avg,
            f"2. {_necessary}": self.expenses_necessary,
            f"3. {_remains} (1 - 2)": self.expenses_free,
            f"4. {_remains} ({_from_tables})": self.expenses_regular,
            f"5. {_full} (1 + 4)": self.expenses_full,
            f"6. {_incomes} - {_full} (1 - 5)": self.expenses_remains,
            f"7. {_sum_per_day} (3 / {_days_in_month})": self.day_calced,
            f"8. {_residual} (3 - 7 * {_days_in_month})": self.remains,
        }

    def get_row(self, name: str) -> int | dict:
        if not self._calculated:
            df = self._create_df()
            self.df = self._calculate_df(df)
            self._calculated = True

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
        ``{"1": 1500, "2": 1600, ..., "12": 1400}``.
        """

        return (
            data.select(pl.first(str(self.month))).item()
            if self.month
            else data.select(MONTH_NUMS).to_dicts()[0]
        )

    def _create_data(self):
        return list(
            it.chain(
                [{"name": InputRow.INCOMES, **d} for d in self._data.incomes],
                [{"name": InputRow.SAVINGS, **d} for d in self._data.savings],
                [{"name": InputRow.PER_DAY, **d} for d in self._data.per_day],
                [
                    {"name": InputRow.EXPENSES_NECESSARY, **d}
                    for d in self._data.expenses_necessary
                ],
                [
                    {"name": InputRow.EXPENSES_REGULAR, **d}
                    for d in self._data.expenses_regular
                ],
                [{"name": InputRow.NECESSARY, **d} for d in self._data.necessary],
                [{"name": InputRow.MONTH_LEN, **d} for d in self._data.month_len],
            )
        )

    def _create_df(self) -> pl.DataFrame:
        data = self._create_data()

        df = pl.DataFrame(data)
        df = df.pivot(values="amount", index="month", on="name").fill_null(0)

        for col in list(InputRow):
            if col in df.columns:
                continue
            df = df.with_columns(pl.lit(0).alias(col))
        return df

    def _calculate_df(self, df):
        return (
            df.lazy()
            .with_columns(
                (pl.col(InputRow.INCOMES).median()).alias(CalcRow.INCOMES_AVG),
                (
                    pl.col(InputRow.EXPENSES_NECESSARY)
                    + pl.col(InputRow.SAVINGS)
                    + pl.col(InputRow.NECESSARY)
                ).alias(CalcRow.EXPENSES_NECESSARY),
            )
            .with_columns(
                (
                    pl.col(CalcRow.INCOMES_AVG) - pl.col(CalcRow.EXPENSES_NECESSARY)
                ).alias(CalcRow.EXPENSES_FREE),
                (
                    pl.col(CalcRow.EXPENSES_NECESSARY)
                    + pl.col(InputRow.EXPENSES_REGULAR)
                ).alias(CalcRow.EXPENSES_FULL),
            )
            .with_columns(
                (pl.col(CalcRow.EXPENSES_FREE) / pl.col(InputRow.MONTH_LEN)).alias(
                    CalcRow.PER_DAY
                ),
                (
                    pl.col(CalcRow.EXPENSES_FREE)
                    - (pl.col(InputRow.PER_DAY) * pl.col(InputRow.MONTH_LEN))
                ).alias(CalcRow.REMAINS),
                (pl.col(CalcRow.INCOMES_AVG) - pl.col(CalcRow.EXPENSES_FULL)).alias(
                    CalcRow.EXPENSES_REMAINS
                ),
            )
            .collect()
            .sort("month")
            .drop("month")
            .transpose(include_header=True, header_name="name", column_names=MONTH_NUMS)
        )
