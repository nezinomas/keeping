import itertools as it
from dataclasses import dataclass, field
from operator import itemgetter

from django.utils.translation import gettext as _

from ...core.lib.date import current_day
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum
from ...savings.models import Saving
from ..lib.balance_base import BalanceBase
from ..lib.day_spending import DaySpending


@dataclass
class MonthServiceData:
    year: int
    month: int

    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    expense_types: list = field(init=False, default_factory=list)
    necessary_expense_types: list = field(init=False, default_factory=list)
    savings: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = list(Income.objects.sum_by_month(self.year, self.month))

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

    def chart_targets_context(self):
        total_row = self._get_total_row_with_savings(self._spending.total_row)
        categories, data_target, data_fact = self._chart_data_for_targets(
            total_row, self._plans.targets
        )

        return {
            "categories": categories,
            "target": data_target,
            "targetTitle": _("Plan"),
            "fact": data_fact,
            "factTitle": _("Fact"),
        }

    def chart_expenses_context(self):
        total_row_with_savings = self._get_total_row_with_savings(
            self._spending.total_row
        )
        return self._chart_data_for_expenses(total_row_with_savings)

    def info_context(self):
        fact_incomes = self._get_fact_income()
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

    def month_table_context(self) -> dict:
        return {
            "day": current_day(self._data.year, self._data.month, False),
            "expenses": self._generate_expenses_table(),
            "expense_types": self._data.expense_types,
            "total": self._spending.total,
            "total_row": self._spending.total_row,
            "total_savings": self._savings.total,
        }

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

    def _generate_expenses_table(self) -> list[tuple]:
        return it.zip_longest(
            self._spending.balance,
            self._spending.total_column,
            self._spending.spending,
            self._savings.total_column,
        )

    def _get_total_row_with_savings(self, total_row: dict) -> dict:
        return self._append_to_data_dict(total_row, _("Savings"), self._savings.total)

    def _append_to_data_dict(self, data: dict, title: str, value: float) -> dict:
        if isinstance(data, dict):
            value = value or 0
            data[title] = value
        return data

    def _get_fact_income(self) -> float:
        fact_incomes = self._data.incomes
        return float(fact_incomes[0]["sum"]) if fact_incomes else 0

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
