from dataclasses import dataclass

import polars as pl
from django.db.models import QuerySet, Sum

from ...accounts.models import AccountBalance
from ...core.lib.date import monthnames
from ...expenses.models import Expense
from ...incomes.models import Income
from ...plans.models import IncomePlan
from ...savings.models import Saving


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

    def _make_data(self, data: QuerySet) -> list[int]:
        """
        Generates price array based on the given data.

        Args:
            data (list): A list of dictionaries containing the data.
            [{"date": date, "sum": sum, "title": title},]

        Returns:
            list: The generated price array for 12 months.
            If month does not exist in the data, price will be 0.
        """
        arr = [0] * 12

        for row in data:
            month = row["date"].month
            arr[month - 1] = row["sum"]

        return arr

    def _make_planned_data(self, data: QuerySet) -> list[int]:
        """
        Calculates the total price for each month in a given dataset.

        Args:
            data (QuerySet): The dataset containing rows of monthly prices.

        Returns:
            list[int]: A list of total prices for each month, where the index represents the month (0-11).
            If the month does not exist in the dataset, the price will be 0.
        """

        arr = [0] * 12
        month_map = dict(zip(monthnames(), range(1, 13)))

        for row in data:
            for month, price in row.items():
                if not price:
                    continue

                month_index = month_map[month] - 1
                arr[month_index] += price
        return arr


class ForecastService:
    def __init__(self, month, data):
        self._month = month
        self._data = self._create_df(data)

    def _create_df(self, data):
        return pl.DataFrame(data | {"month": list(range(1, 13))})

    def balance(self):
        df = (
            self._data
            .filter(pl.col("month") < self._month)
            .sum()
            .with_columns(
                (pl.col("incomes") - pl.col("expenses") - pl.col("savings")).alias("balance")
            )
        )
        return df["balance"].to_list()[0]

    def planned_incomes(self):
        df = (
            self._data
            .filter(pl.col("month") >= self._month)
            .select(pl.col("planned_incomes"))
            .sum()
        )
        return df[0, 0]

    def averages(self):
        return (
            self._data
            .filter(pl.col("month") <= self._month - 1)
            .select([pl.col.expenses, pl.col.savings])
            .mean()
            .to_dicts()[0]
        )

    def current_month(self):
        return (
            self._data
            .filter(pl.col("month") == self._month)
            .select([pl.col.expenses, pl.col.savings])
            .to_dicts()[0]
        )

    def forecast(self):
        month_left = 12 - self._month
        avg = self.averages()
        current = self.current_month()

        total = self.balance() + self.planned_incomes()
        for key in ["expenses", "savings"]:
            avg_value = avg[key]
            current_value = max(current[key], avg_value)
            total -= current_value + avg_value * month_left

        return total


def load_service(year: int, month: int) -> dict:
    data = ForecastServiceData(year)
    forecast = ForecastService(month, data.data()).forecast()

    beginning = data.amount_at_beginning_of_year()
    end = beginning + forecast

    return {
        "data": [beginning, end, forecast],
        "highlight": [False, False, True],
    }
