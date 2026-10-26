import calendar
from dataclasses import dataclass
from enum import StrEnum

import polars as pl

from ...users.models import User
from ..services.model_services import (
    DayPlanModelService,
    ExpensePlanModelService,
    IncomePlanModelService,
    NecessaryPlanModelService,
    SavingPlanModelService,
)
from .month_states import MONTH_NUMS, OVER, WITHIN


class InputRow(StrEnum):
    """Raw data categories provided by the SQL Database."""

    INCOMES = "incomes"
    SAVINGS = "savings"
    DAY_PLAN = "day_input"
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
    SUM_PER_DAY = "day_calced"
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
            expenses_regular=expenses_service.everyday_by_month(self.year),
            expenses_necessary=expenses_service.necessary_by_month(self.year),
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

    def day_plan_states(self) -> dict[str, str]:
        day_plan = self.row(InputRow.DAY_PLAN)
        sum_per_day = self.row(CalcRow.SUM_PER_DAY)

        return {
            month: OVER
            if day_plan[month] and day_plan[month] > sum_per_day[month]
            else WITHIN
            for month in MONTH_NUMS
        }

    def row(self, name: CalcRow | InputRow) -> int | dict:
        if not self._calculated:
            df = self._create_df()
            self.df = self._calculate_df(df)
            self._calculated = True

        data = self.df.filter(pl.col("name") == name)

        return self._return_data(data)

    def _return_data(self, data: pl.DataFrame) -> int | dict:
        return (
            data.select(pl.first(str(self.month))).item()
            if self.month
            else data.select(MONTH_NUMS).to_dicts()[0]
        )

    def _create_data(self):
        table = {
            InputRow.INCOMES: self._data.incomes,
            InputRow.SAVINGS: self._data.savings,
            InputRow.DAY_PLAN: self._data.per_day,
            InputRow.EXPENSES_NECESSARY: self._data.expenses_necessary,
            InputRow.EXPENSES_REGULAR: self._data.expenses_regular,
            InputRow.NECESSARY: self._data.necessary,
            InputRow.MONTH_LEN: self._data.month_len,
        }
        return [{"name": name, **row} for name, rows in table.items() for row in rows]

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
                    CalcRow.SUM_PER_DAY
                ),
                (
                    pl.col(CalcRow.EXPENSES_FREE)
                    - (pl.col(InputRow.DAY_PLAN) * pl.col(InputRow.MONTH_LEN))
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
