from dataclasses import dataclass

import polars as pl
from django.db.models import QuerySet, Sum

from ...accounts.models import AccountBalance
from ...core.lib.date import monthnames
from ...expenses.models import Expense
from ...incomes.models import Income
from ...plans.models import IncomePlan
from ...savings.models import Saving
from ...transactions.models import SavingClose


@dataclass
class ForecastServiceData:
    year: int

    def data(self) -> dict[str, list[int]]:
        incomes = self._make_data(Income.objects.sum_by_month(self.year))
        expenses = self._make_data(Expense.objects.sum_by_month(self.year))
        savings = self._make_data(Saving.objects.sum_by_month(self.year))
        savings_close = self._make_data(SavingClose.objects.sum_by_month(self.year))
        planned_incomes = self._make_planned_data(
            IncomePlan.objects.year(self.year).values(*monthnames())
        )
        return {
            "incomes": incomes,
            "expenses": expenses,
            "savings": savings,
            "savings_close": savings_close,
            "planned_incomes": planned_incomes,
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
        Takes a QuerySet object and converts it into a list of integers.

        Parameters:
            data (QuerySet): The QuerySet object containing the data to be converted.

        Returns:
            list[int]: A list of integers representing the data from the QuerySet object.
            If month does not exist in the dataset, the price will be 0.
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
    def __init__(self, month: int, data: dict[str, list[int]]):
        self._month = month
        self._data = self._create_df(data)

    def _create_df(self, data: dict[str, list[int]]) -> pl.DataFrame:
        return pl.DataFrame(data | {"month": list(range(1, 13))})

    def balance(self) -> int:
        """
        Calculates balance from January to current month, excluding current month.

        Returns:
            int: The balance for the current month.

            Formula: incomes + savings_close - expenses - savings
        """
        df = (
            self._data.filter(pl.col("month") < self._month)
            .sum()
            .with_columns(
                balance=(
                    pl.col("incomes")
                    + pl.col("savings_close")
                    - pl.col("expenses")
                    - pl.col("savings")
                )
            )
        )
        return df["balance"].to_list()[0]

    def planned_incomes(self) -> int:
        """
        Calculate the total sum of planned incomes from current month to December.

        Returns:
            int: The total sum of planned incomes.
        """
        df = (
            self._data.filter(pl.col("month") >= self._month)
            .select(pl.col("planned_incomes"))
            .sum()
        )
        return df[0, 0]

    def averages(self) -> dict:
        """
        Calculates the average expenses and savings for the months from January to the current month.

        Returns:
            A dictionary containing the average expenses and savings.

            The keys are "expenses" and "savings".

            {"expenses": int, "savings": int}
        """
        return (
            self._data.filter(pl.col("month") <= self._month - 1)
            .select([pl.col.expenses, pl.col.savings])
            .mean()
            .fill_null(0)
            .to_dicts()[0]
        )

    def current_month(self) -> dict:
        """
        Calculates expenses and savings for the current month.

        Returns:
            A dictionary containing sum of expenses and savings.

            The keys are "expenses" and "savings".

            {"expenses": int, "savings": int}
        """
        return (
            self._data.filter(pl.col("month") == self._month)
            .select([pl.col.expenses, pl.col.savings])
            .to_dicts()[0]
        )

    def forecast(self) -> int:
        """
        Calculate the forecasted balance for the end of the year.

        Returns:
            int: The forecasted balance for the end of the year.
        """
        avg = self.averages()
        current = self.current_month()

        expenses_avg = avg["expenses"]
        expenses_current = max(current["expenses"], expenses_avg)

        savings_avg = avg["savings"]
        savings_current = max(current["savings"], savings_avg)

        month_left = 12 - self._month

        return (
            0
            + self.balance()
            + self.planned_incomes()
            - (expenses_current + expenses_avg * month_left)
            - (savings_current + savings_avg * month_left)
        )

def load_service(year: int, month: int) -> dict:
    data = ForecastServiceData(year)
    forecast = ForecastService(month, data.data()).forecast()

    beginning = data.amount_at_beginning_of_year()
    end = beginning + forecast

    return {
        "data": [beginning, end, forecast],
        "highlight": [False, False, True],
    }
