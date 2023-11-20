import contextlib
import itertools as it
from dataclasses import asdict, dataclass, field
from operator import itemgetter

import polars as pl
from django.db.models import Sum
from django.utils.translation import gettext as _

from ...core.lib.date import current_day
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData
from ...savings.models import Saving
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


class Charts:
    def __init__(
        self,
        targets_with_savings: dict,
        total_row_with_savings: dict
    ):
        with contextlib.suppress(KeyError):
            del total_row_with_savings[_("Total")]

        self._totals_with_savings = total_row_with_savings
        self._targets_with_savings = targets_with_savings


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


def info_table(income: int, total: dict, per_day: int, plans: PlanCalculateDaySum) -> dict:
    expense = total.get(_("Total"), 0)
    saving = total.get(_("Savings"), 0)

    fact = Info(
        income=income,
        expense=expense,
        saving=saving,
        per_day=per_day,
        balance=(income - expense - saving),
    )

    plan = Info(
        income=plans.incomes,
        expense=(plans.incomes - plans.savings),
        saving=plans.savings,
        per_day=plans.day_input,
        balance=plans.remains,
    )

    delta = plan - fact

    return {"plan": asdict(plan), "fact": asdict(fact), "delta": asdict(delta)}


def load_service(year: int, month: int) -> dict:
    # get data from db
    data = MonthServiceData(year, month)

    # expense and saving data_frames
    expense = MakeDataFrame(year, data.expenses, data.expense_types, month)
    saving = MakeDataFrame(year, data.savings, None, month)

    # plans
    plans = PlanCalculateDaySum(PlanCollectData(year, month))

    # spending table
    spending = DaySpending(
        df=expense,
        necessary=data.necessary_expense_types,
        day_input=plans.day_input,
        expenses_free=plans.expenses_free,
    )

    # main table
    main_table = MainTable(expense, saving)

    # charts
    charts = Charts(
        targets_with_savings=(plans.targets | {_("Savings"): plans.savings}),
        total_row_with_savings=main_table.total_row
    )

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
        "info": info_table(
            data.incomes, main_table.total_row, spending.avg_per_day, plans
        ),
        "chart_expenses": charts.chart_expenses_context(),
        "chart_targets": charts.chart_targets_context(),
    }
