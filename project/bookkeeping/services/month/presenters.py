from functools import cached_property

from django.utils.translation import gettext_lazy as _

from ....plans.lib.calc_day_sum import PlanCalculateDaySum
from ...lib.day_spending import DaySpending
from ...lib.make_dataframe import MakeDataFrame
from .builders import ChartBuilder, InfoBuilder, MonthTableBuilder
from .dtos import InfoState, MonthDataDTO


class MonthContextPresenter:
    def __init__(self, year, month, dto: MonthDataDTO):
        self.year = year
        self.month = month
        self.dto = dto

    @cached_property
    def month_table(self) -> MonthTableBuilder:
        expense_df_object = MakeDataFrame(
            year=self.year,
            month=self.month,
            data=self.dto.expenses,
            columns=self.dto.expense_types,
        )
        saving_df_object = MakeDataFrame(
            year=self.year, month=self.month, data=self.dto.savings
        )
        return MonthTableBuilder(expense_df_object.data, saving_df_object.data)

    @cached_property
    def plans(self) -> PlanCalculateDaySum:
        return PlanCalculateDaySum(data=self.dto.plans_data, month=self.month)

    @cached_property
    def spending(self) -> DaySpending:
        expense_df_object = MakeDataFrame(
            year=self.year,
            month=self.month,
            data=self.dto.expenses,
            columns=self.dto.expense_types,
        )
        return DaySpending(
            expense=expense_df_object,
            necessary=self.dto.necessary_expense_types,
            per_day=self.plans.day_input,
            free=self.plans.expenses_free,
        )

    @cached_property
    def totals(self) -> dict:
        _exp = self.month_table.total_row.get("total", 0)
        _sav = self.month_table.total_row.get("savings", 0)

        return {
            "income": self.dto.incomes,
            "expense": _exp,
            "saving": _sav,
            "avg_per_day": self.spending.avg_per_day,
        }

    @cached_property
    def tables(self) -> dict:
        return {
            "main_table": self.month_table.table,
            "spending_table": self.spending.spending,
            "total_row": self.month_table.total_row,
        }

    @cached_property
    def info_context(self) -> dict:
        fact_state = InfoState(
            income=self.totals["income"],
            expense=self.totals["expense"],
            saving=self.totals["saving"],
            per_day=self.totals["avg_per_day"],
            balance=(
                self.totals["income"] - self.totals["expense"] - self.totals["saving"]
            ),
        )

        plan_state = InfoState(
            income=self.plans.incomes,
            expense=(
                self.plans.expenses_necessary
                + self.plans.expenses_free
                - self.plans.savings
            ),
            saving=self.plans.savings,
            per_day=self.plans.day_input,
            balance=self.plans.remains,
        )

        return InfoBuilder.build(fact=fact_state, plan=plan_state)

    @cached_property
    def charts(self) -> ChartBuilder:
        return ChartBuilder(targets=self.dto.targets, totals=self.month_table.total_row)
