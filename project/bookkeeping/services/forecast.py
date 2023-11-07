import polars as pl
from dataclasses import dataclass

from django.db.models import Sum

from ...accounts.models import AccountBalance
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ...plans.models import IncomePlan
from ...core.lib.date import monthnames


@dataclass
class ForecastServiceData:
    year: int

    def data(self):
        return {
            "incomes": self._make_data(Income.objects.sum_by_month(self.year)),
            "expenses": self._make_data(Expense.objects.sum_by_month(self.year)),
            "savings": self._make_data(Saving.objects.sum_by_month(self.year)),
            "planned_incomes": self._make_planned_data(
                IncomePlan.objects.year(self.year).values(*monthnames())
            ),
        }

    def amount_at_beginning_of_year(self) -> int:
        return (
            AccountBalance.objects.related()
            .filter(year=self.year)
            .aggregate(Sum("past"))["past__sum"]
            or 0
        )

    def _make_data(self, data):
        arr = [0] * 12

        for row in data:
            month = row["date"].month
            arr[month - 1] = row["sum"]

        return arr

    def _make_planned_data(self, data):
        arr = [0] * 12
        month_map = {month: i for i, month in enumerate(monthnames(), 1)}

        for row in data:
            for k, v in row.items():
                if not v:
                    continue

                month = month_map[k]
                arr[month - 1] += v
        return arr


class ForecastService:
    def __init__(self, month, data):
        self._month = month
        self._data = self._create_df(data)

    def _create_df(self, data):
        return pl.DataFrame(data | {"month": list(range(1, 13))})

    def balance(self):
        df = (
            self._data.filter(pl.col("month") < self._month)
            .sum()
            .with_columns(
                (pl.col("incomes") - pl.col("expenses") - pl.col("savings")).alias(
                    "balance"
                )
            )
        )
        return df.select(pl.col("balance")).to_series().to_list()[0]

    def planned_incomes(self):
        df = (
            self._data.filter(pl.col("month") >= self._month)
            .select(pl.col("planned_incomes"))
            .sum()
        )
        return df[0, 0]

    def averages(self):
        min_ = 0 if self._month < 3 else self._month - 3
        max_ = self._month - 1
        df = self._data.filter(
            (pl.col("month") >= min_) & ((pl.col("month") <= max_))
        ).mean()
        return {"expenses": df["expenses"][0], "savings": df["savings"][0]}

    def forecast(self):
        month_left = 12 - self._month + 1
        averages = self.averages()

        return (
            0.0
            + self.balance()
            + self.planned_incomes()
            - averages["expenses"] * month_left
            - averages["savings"] * month_left
        )
