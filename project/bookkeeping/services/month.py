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
from ...plans.services.model_services import PlanAggregatorService
from ...savings.services.model_services import SavingModelService
from ...users.models import User
from ..lib.day_spending import DaySpending
from ..lib.make_dataframe import MakeDataFrame


@dataclass(frozen=True)
class MonthDataDTO:
    incomes: int
    expenses: list[dict]
    expense_types: list[str]
    necessary_expense_types: list[str]
    savings: list[dict]


class MonthDataProvider:
    def __init__(self, user: User):
        self.user = user
        self.year = user.year
        self.month = user.month

    def get_data(self) -> MonthDataDTO:
        return MonthDataDTO(
            incomes=self._get_incomes(),
            expenses=list(
                ExpenseModelService(self.user).sum_by_day_and_type(
                    self.year, self.month
                )
            ),
            expense_types=list(
                ExpenseTypeModelService(self.user).objects.values_list(
                    "title", flat=True
                )
            ),
            necessary_expense_types=list(
                ExpenseTypeModelService(self.user)
                .objects.filter(necessary=True)
                .values_list("title", flat=True)
            ),
            savings=list(
                SavingModelService(self.user).sum_by_day(self.year, self.month)
            ),
        )

    def _get_incomes(self) -> int:
        return (
            IncomeModelService(self.user)
            .objects.filter(date__year=self.year, date__month=self.month)
            .aggregate(Sum("price", default=0))["price__sum"]
        )


class MonthTableBuilder:
    """Merges expenses and savings into a single Polars DataFrame representing the month."""

    def __init__(self, expense_df: pl.DataFrame, saving_df: pl.DataFrame):
        self.df = self._build_table(expense_df, saving_df)

    def _build_table(
        self, expense_df: pl.DataFrame, saving_df: pl.DataFrame
    ) -> pl.DataFrame:
        # If exists at least two columns (date + at least one expense type), create total column
        if expense_df.shape[1] > 1:
            expense_df = expense_df.with_columns(
                pl.sum_horizontal(pl.exclude("date")).alias(_("Total"))
            )

        return expense_df.join(
            saving_df, on="date", how="full", coalesce=True, nulls_equal=True
        )

    @property
    def table(self) -> list[dict]:
        return [] if self.df.is_empty() else self.df.to_dicts()

    @property
    def total_row(self) -> dict:
        if self.df.is_empty() or self.df.shape[1] == 1:
            return {}
        return self.df.select(pl.exclude("date")).sum().to_dicts()[0]


class ChartBuilder:
    """Formats financial data specifically for frontend charts."""

    def __init__(self, targets: dict, totals: dict):
        self.totals = {k: v for k, v in totals.items() if k != _("Total")}
        self.targets = targets

    def build_targets(self) -> dict:
        data = self._sort_chart_data(self.totals)
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

    def build_expenses(self) -> list[dict]:
        data = self._sort_chart_data(self.totals)
        for entry in data:
            entry["name"] = entry["name"].upper()
        return data

    def _sort_chart_data(self, data: dict) -> list[dict]:
        return sorted(
            [{"name": key, "y": val} for key, val in data.items()],
            key=itemgetter("y"),
            reverse=True,
        )


@dataclass(frozen=True)
class InfoState:
    income: int
    saving: int
    expense: int
    per_day: int
    balance: int


class InfoBuilder:
    @staticmethod
    def build(fact: InfoState, plan: InfoState) -> dict:
        delta = InfoState(
            income=fact.income - plan.income,
            saving=plan.saving - fact.saving,
            expense=plan.expense - fact.expense,
            per_day=plan.per_day - fact.per_day,
            balance=fact.balance - plan.balance,
        )

        return {"plan": asdict(plan), "fact": asdict(fact), "delta": asdict(delta)}


class MonthContextPresenter:
    def __init__(self, user: User, dto: MonthDataDTO):
        self.year = user.year
        self.month = user.month
        self.dto = dto

        expense_maker = MakeDataFrame(
            year=self.year,
            month=self.month,
            data=dto.expenses,
            columns=dto.expense_types,
        )

        saving_maker = MakeDataFrame(year=self.year, month=self.month, data=dto.savings)

        # 2. Initialize Core Services
        plans_data = PlanCollectData(user, self.year).get_data()
        self.plans = PlanCalculateDaySum(data=plans_data, month=self.month)

        self.spending = DaySpending(
            expense=expense_maker,
            necessary=dto.necessary_expense_types,
            per_day=self.plans.day_input,
            free=self.plans.expenses_free,
        )
        self.month_table = MonthTableBuilder(
            expense_df=expense_maker.data, saving_df=saving_maker.data
        )

        self.charts = ChartBuilder(
            targets=PlanAggregatorService(user).get_monthly_plan_targets(
                self.year, self.month
            ),
            totals=self.month_table.total_row,
        )

    def _build_info_context(self) -> dict:
        """Isolates the messy InfoState instantiation."""
        total_exp = self.month_table.total_row.get(_("Total"), 0)
        total_sav = self.month_table.total_row.get(_("Savings"), 0)

        fact_state = InfoState(
            income=self.dto.incomes,
            expense=total_exp,
            saving=total_sav,
            per_day=self.spending.avg_per_day,
            balance=(self.dto.incomes - total_exp - total_sav),
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

    def to_dict(self) -> dict:
        return {
            "month_table": {
                "day": current_day(self.year, self.month, False),
                "expenses": it.zip_longest(
                    self.month_table.table, self.spending.spending
                ),
                "expense_types": self.dto.expense_types,
                "total_row": self.month_table.total_row,
            },
            "info": self._build_info_context(),
            "chart_expenses": self.charts.build_expenses(),
            "chart_targets": self.charts.build_targets(),
        }


def load_service(user: User) -> dict:
    dto = MonthDataProvider(user).get_data()
    presenter = MonthContextPresenter(user, dto)

    return presenter.to_dict()
