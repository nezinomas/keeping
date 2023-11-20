import itertools as it
from dataclasses import dataclass, field
from operator import itemgetter

import polars as pl
from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib.date import current_day
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData
from ...savings.models import Saving
from ..lib.balance_base import BalanceBase
from ..lib.day_spending import DaySpending
from ..lib.make_dataframe import MakeDataFrame


@dataclass
class MonthServiceData:
    year: int
    month: int

    incomes: int = field(init=False, default=0)
    expenses: list[dict] = field(init=False, default_factory=list)
    expense_types: list = field(init=False, default_factory=list)
    necessary_expense_types: list = field(init=False, default_factory=list)
    savings: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = (
            Income.objects.related()
            .filter(date__year=self.year, date__month=self.month)
            .aggregate(Sum("price", default=0))["price__sum"]
        )

        self.expenses = list(Expense.objects.sum_by_day_ant_type(self.year, self.month))

        self.expense_types = list(
            ExpenseType.objects.items().values_list("title", flat=True)
        )

        self.necessary_expense_types = list(
            ExpenseType.objects.items()
            .filter(necessary=True)
            .values_list("title", flat=True)
        )

        self.savings = list(Saving.objects.sum_by_day(self.year, self.month))


class MonthService:
    def __init__(
        self,
        data: MonthServiceData,
        plans: PlanCalculateDaySum,
        savings: BalanceBase,
        spending: DaySpending,
    ):
        self._data = data
        self._plans = plans
        self._spending = spending
        self._savings = savings

        # push savings data
        self._totals_with_savings = spending.total_row | {_("Savings"): savings.total}
        self._targets_with_savings = plans.targets | {_("Savings"): plans.savings}

    def chart_targets_context(self):
        categories, data_target, data_fact = self._chart_data_for_targets(
            self._totals_with_savings, self._targets_with_savings
        )

        return {
            "categories": categories,
            "target": data_target,
            "targetTitle": _("Plan"),
            "fact": data_fact,
            "factTitle": _("Fact"),
        }

    def chart_expenses_context(self):
        return self._chart_data_for_expenses(self._totals_with_savings)

    def info_context(self):
        fact_incomes = self._data.incomes
        fact_savings = self._savings.total
        fact_expenses = self._spending.total
        fact_per_day = self._spending.avg_per_day
        fact_balance = self._calculate_balance(
            fact_incomes, fact_expenses, fact_savings
        )

        plan_incomes = self._plans.incomes
        plan_savings = self._plans.savings
        plan_expenses = self._calculate_expenses(plan_incomes, plan_savings)
        plan_per_day = self._plans.day_input
        plan_balance = self._plans.remains

        return self._generate_info_entries(
            (_("Incomes"), plan_incomes, fact_incomes),
            (_("Expenses"), plan_expenses, fact_expenses),
            (_("Savings"), plan_savings, fact_savings),
            (_("Money for a day"), plan_per_day, fact_per_day),
            (_("Balance"), plan_balance, fact_balance),
        )

    def _chart_data_for_expenses(self, total_row: dict) -> list[dict]:
        data = self._make_chart_data(total_row)
        for entry in data:
            entry["name"] = entry["name"].upper()
        return data

    def _chart_data_for_targets(
        self, total_row: dict, targets: dict
    ) -> tuple[list[str], list[float], list[dict]]:
        data = self._make_chart_data(total_row)

        rtn_categories, rtn_data_fact, rtn_data_target = [], [], []

        for entry in data:
            category = entry["name"]
            target = float(targets.get(category, 0))
            fact = float(entry["y"])

            rtn_categories.append(category.upper())
            rtn_data_target.append(target)
            rtn_data_fact.append({"y": fact, "target": target})

        return (rtn_categories, rtn_data_target, rtn_data_fact)

    def _make_chart_data(self, data: dict) -> list[dict]:
        rtn = []
        for key, val in data.items():
            rtn.append({"name": key, "y": val})

        if rtn:
            rtn = sorted(rtn, key=itemgetter("y"), reverse=True)

        return rtn

    def _generate_info_entries(self, *entries) -> list[dict]:
        return [
            {"title": title, "plan": plan, "fact": fact}
            for title, plan, fact in entries
        ]

    def _calculate_balance(
        self, incomes: float, expenses: float, savings: float
    ) -> float:
        return incomes - expenses - savings

    def _calculate_expenses(self, incomes: float, savings: float) -> float:
        return incomes - savings


class MainTable:
    def __init__(self, expense: MakeDataFrame, saving: MakeDataFrame):
        self.df = self.make_table(expense, saving)

    def make_table(self, expense, saving):
        df_expense = expense.data

        # if exists only one column (dates) i.e. there are no expense_types
        if df_expense.shape[1] > 1:
            df_expense = df_expense.with_columns(
                pl.sum_horizontal(pl.exclude("date")).alias(_("Total"))
            )

        return df_expense.join(saving.data, on="date", how="outer")

    @property
    def table(self):
        return [] if self.df.is_empty() else self.df.to_dicts()

    @property
    def total_row(self):
        return (
            {}
            if self.df.is_empty()
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



def load_service(year: int, month: int) -> dict:
    data = MonthServiceData(year, month)
    expense = MakeDataFrame(year, data.expenses, data.expense_types, month)
    saving = MakeDataFrame(year, data.savings, None, month)

    plans = PlanCalculateDaySum(PlanCollectData(year, month))
    spending = DaySpending(
        df=expense,
        necessary=data.necessary_expense_types,
        day_input=plans.day_input,
        expenses_free=plans.expenses_free,
    )

    savings = BalanceBase(saving.data)

    service = MonthService(
        data=data,
        plans=plans,
        savings=savings,
        spending=spending,
    )

    main_table = MainTable(expense, saving)

    return {
        "month_table": {
            "day": current_day(year, month, False),
            "expenses": it.zip_longest(
                main_table.table,
                spending.spending,
            ),
            "expense_types": data.expense_types,
            "total_row": main_table.total_row,
        },
        "info": service.info_context(),
        "chart_expenses": service.chart_expenses_context(),
        "chart_targets": service.chart_targets_context(),
    }
