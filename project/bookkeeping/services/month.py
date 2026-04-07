import contextlib
import itertools as it
from dataclasses import asdict, dataclass
from operator import itemgetter

import polars as pl
from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib.date import current_day
from ...expenses.services.model_services import (
    ExpenseModelService,
    ExpenseTypeModelService,
)
from ...incomes.services.model_services import IncomeModelService
from ...plans.lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData
from ...savings.services.model_services import SavingModelService
from ..lib.day_spending import DaySpending
from ..lib.make_dataframe import MakeDataFrame


@dataclass(frozen=True)
class DataDto:
    incomes: int
    expenses: list[dict]
    expense_types: list
    necessary_expense_types: list
    savings: list


class Charts:
    def __init__(self, targets: dict, totals: dict):
        self.totals = self._filter_totals(totals)
        self.targets = targets

    def chart_targets(self) -> dict:
        data = self._make_chart_data(self.totals)

        categories, data_fact, data_target = [], [], []

        for entry in data:
            category = entry["name"]
            target = self.targets.get(category, 0)
            fact = entry["y"]

            categories.append(category.upper())
            data_target.append(target)
            data_fact.append({"y": fact, "target": target})

        return {
            "categories": categories,
            "target": data_target,
            "targetTitle": _("Plan"),
            "fact": data_fact,
            "factTitle": _("Fact"),
            "max_category_len": len(max(categories, key=len)) if categories else 0,
            "category_len": len(categories),
        }

    def chart_expenses(self) -> list[dict]:
        data = self._make_chart_data(self.totals)

        for entry in data:
            entry["name"] = entry["name"].upper()
        return data

    def _filter_totals(self, totals: dict) -> dict:
        with contextlib.suppress(KeyError):
            del totals[_("Total")]
        return totals

    def _make_chart_data(self, data: dict) -> list[dict]:
        return sorted(
            [{"name": key, "y": val} for key, val in data.items()],
            key=itemgetter("y"),
            reverse=True,
        )


class MainTable:
    def __init__(self, expense: MakeDataFrame, saving: MakeDataFrame):
        self.df = self.make_table(expense, saving)

    def make_table(self, expense, saving):
        df_expense = expense.data

        # if exists at least two columns (dates, expense_type) create total column
        if df_expense.shape[1] > 1:
            df_expense = df_expense.with_columns(
                pl.sum_horizontal(pl.exclude("date")).alias(_("Total"))
            )

        return df_expense.join(
            saving.data, on="date", how="full", coalesce=True, nulls_equal=True
        )

    @property
    def table(self):
        return [] if self.df.is_empty() else self.df.to_dicts()

    @property
    def total_row(self):
        return (
            {}
            if self.df.is_empty() or self.df.shape[1] == 1
            else self.df.select(pl.exclude("date")).sum().to_dicts()[0]
        )


@dataclass
class Info:
    income: int
    saving: int
    expense: int
    per_day: int
    balance: int

    def __sub__(self, other):
        return __class__(
            other.income - self.income,
            self.saving - other.saving,
            self.expense - other.expense,
            self.per_day - other.per_day,
            other.balance - self.balance,
        )


class Objects:
    def __init__(self, user, data: DataDto):
        self.user = user
        self.data: DataDto = data

        # cash expenses calculation
        self.expenses = MakeDataFrame(
            year=self.user.year,
            month=self.user.month,
            data=self.data.expenses,
            columns=self.data.expense_types,
        )

        self.plans: PlanCalculateDaySum = self._initialize_plans()
        self.spending: DaySpending = self._initialize_spending()
        self.main_table: MainTable = self._initialize_main_table()
        self.charts: Charts = self._initialize_charts()

    def _initialize_plans(self) -> PlanCalculateDaySum:
        return PlanCalculateDaySum(
            data=PlanCollectData(self.user), month=self.user.month
        )

    def _initialize_spending(self) -> DaySpending:
        return DaySpending(
            expense=self.expenses,
            necessary=self.data.necessary_expense_types,
            per_day=self.plans.day_input,
            free=self.plans.expenses_free,
        )

    def _initialize_main_table(self) -> MainTable:
        saving = MakeDataFrame(
            year=self.user.year,
            month=self.user.month,
            data=self.data.savings,
        )
        return MainTable(expense=self.expenses, saving=saving)

    def _initialize_charts(self) -> Charts:
        return Charts(
            targets=self.plans.monthly_plan_by_category,
            totals=self.main_table.total_row,
        )

    def info_table(self) -> dict:
        income = self.data.incomes
        expense = self.main_table.total_row.get(_("Total"), 0)
        saving = self.main_table.total_row.get(_("Savings"), 0)

        fact = Info(
            income=income,
            expense=expense,
            saving=saving,
            per_day=self.spending.avg_per_day,
            balance=(income - expense - saving),
        )

        plan = Info(
            income=self.plans.incomes,
            expense=(
                0
                + self.plans.expenses_necessary
                + self.plans.expenses_free
                - self.plans.savings
            ),
            saving=self.plans.savings,
            per_day=self.plans.day_input,
            balance=self.plans.remains,
        )

        delta = plan - fact

        return {"plan": asdict(plan), "fact": asdict(fact), "delta": asdict(delta)}


def load_service(user) -> dict:
    year = user.year
    month = user.month

    data_payload = DataDto(
        incomes = (
                IncomeModelService(user)
                .objects.filter(date__year=year, date__month=month)
                .aggregate(Sum("price", default=0))["price__sum"]
            ),
        expenses = list(
                list(
                    ExpenseModelService(user).sum_by_day_and_type(
                        year, month
                    )
                )
            ),
            expense_types = list(
                ExpenseTypeModelService(user).objects.values_list("title", flat=True)
            ),
            necessary_expense_types = list(
                ExpenseTypeModelService(user)
                .objects.filter(necessary=True)
                .values_list("title", flat=True)
            ),
            savings = list(
                SavingModelService(user).sum_by_day(year, month)
            )
    )

    obj = Objects(user, data_payload)
    return {
        "month_table": {
            "day": current_day(user.year, user.month, False),
            "expenses": it.zip_longest(
                obj.main_table.table,
                obj.spending.spending,
            ),
            "expense_types": data_payload.expense_types,
            "total_row": obj.main_table.total_row,
        },
        "info": obj.info_table(),
        "chart_expenses": obj.charts.chart_expenses(),
        "chart_targets": obj.charts.chart_targets(),
    }
