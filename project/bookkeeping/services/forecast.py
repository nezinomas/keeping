import itertools as it
from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

import polars as pl
from django.db import models
from django.db.models import QuerySet, Sum

from ...accounts.services.model_services import AccountBalanceModelService
from ...core.lib.date import monthnames
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.services.model_services import IncomeModelService
from ...plans.models import IncomePlan
from ...plans.services.model_services import ModelService
from ...savings.services.model_services import SavingModelService
from ...transactions.services.model_services import SavingCloseModelService
from ...users.models import User


@dataclass
class Data:
    user: User
    year: int = field(init=False, default=1974)

    def __post_init__(self):
        self.year = cast(int, self.user.year)

    def data(self) -> dict[str, list[int]]:
        incomes = self._make_data(IncomeModelService(self.user).sum_by_month(self.year))
        expenses = self._make_data(
            ExpenseModelService(self.user).sum_by_month(self.year)
        )
        savings = self._make_data(SavingModelService(self.user).sum_by_month(self.year))
        savings_close = self._make_data(
            SavingCloseModelService(self.user).sum_by_month(self.year)
        )
        planned_incomes = self._make_planned_data(
            ModelService(cast(models.Model, IncomePlan), self.user)
            .year(self.year)
            .values(*monthnames())
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
            AccountBalanceModelService(self.user)
            .objects.filter(year=self.year)
            .aggregate(Sum("past"))["past__sum"]
            or 0
        )

    def _make_data(self, data: QuerySet) -> list[int]:
        """
        Takes a QuerySet object and converts it into a list of integers.

        Parameters:
            data (QuerySet): The QuerySet object containing the data to be converted.

        Returns:
            list[int]: A list of integers representing the data
            from the QuerySet object.
            If month does not exist in the dataset, the price will be 0.
        """

        arr = [0] * 12
        for row in data:
            arr[row["date"].month - 1] = row["sum"]
        return arr

    def _make_planned_data(self, data: QuerySet) -> list[int]:
        """
        Calculates the total price for each month in a given dataset.

        Args:
            data (QuerySet): The dataset containing rows of monthly prices.

        Returns:
            list[int]: A list of total prices for each month,
            where the index represents the month (0-11).
            If the month does not exist in the dataset, the price will be 0.
        """

        monthly_totals = [0] * 12
        month_map = {name: idx for idx, name in enumerate(monthnames())}

        for month, price in it.chain.from_iterable(row.items() for row in data):
            if not price or month not in month_map:
                continue
            monthly_totals[month_map[month]] += price

        return monthly_totals


class Forecast:
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
        Current month not included.

        Returns:
            int: The total sum of planned incomes.
        """

        df = (
            self._data.filter(pl.col("month") > self._month)
            .select(pl.col("planned_incomes"))
            .sum()
        )
        return df[0, 0]

    def medians(self) -> dict:
        """
        Calculates median expenses and savings for the months
        from January to the current month.
        Current month not included.

        Returns:
            A dictionary containing median expenses and savings.

            The keys are "expenses" and "savings".

            {"expenses": int, "savings": int}
        """
        return (
            self._data.filter(pl.col("month") < self._month)
            .select([pl.col.expenses, pl.col.savings])
            .median()
            .fill_null(0)
            .to_dicts()[0]
        )

    def current_month(self) -> dict:
        """
        Calculates expenses and savings for the current month.

        Returns:
            A dictionary containing sum of expenses and savings.

            The keys are "expenses", "savings", "incomes", "planed_incomes".

            {"expenses": int, "savings": int, "incomes": int, "planned_incomes": int}
        """
        return (
            self._data.filter(pl.col("month") == self._month)
            .select(
                [
                    pl.col.expenses,
                    pl.col.savings,
                    pl.col.incomes,
                    pl.col.planned_incomes,
                ]
            )
            .to_dicts()[0]
        )

    def forecast(self) -> int:
        """
        Calculate the forecasted balance for the end of the year.

        Returns:
            int: The forecasted balance for the end of the year.
        """
        avg = self.medians()
        current = self.current_month()
        month_left = 12 - self._month

        expenses = max(current["expenses"], avg["expenses"])
        savings = max(current["savings"], avg["savings"])
        incomes = max(current["incomes"], current["planned_incomes"])

        return (
            0
            + self.balance()
            + self.planned_incomes()
            + incomes
            - (expenses + avg["expenses"] * month_left)
            - (savings + avg["savings"] * month_left)
        )


def get_month(year: int) -> int:
    now = datetime.now()

    if year > now.year:
        return 1

    return 12 if year < now.year else now.month


def load_service(user: User) -> dict:
    year = cast(int, user.year)
    data = Data(user)
    month = get_month(year)
    forecast = Forecast(month, data.data()).forecast()

    beginning = data.amount_at_beginning_of_year()
    end = beginning + forecast

    return {
        "data": [beginning, end, forecast],
        "highlight": [False, False, True],
    }
