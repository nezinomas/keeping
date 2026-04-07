import itertools as it
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import cast

import polars as pl
from django.db.models import QuerySet, Sum

from ...accounts.services.model_services import AccountBalanceModelService
from ...core.lib.date import monthnames
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.services.model_services import IncomeModelService
from ...plans.services.model_services import IncomePlanModelService
from ...savings.services.model_services import SavingModelService
from ...transactions.services.model_services import SavingCloseModelService
from ...users.models import User

MONTH_NAMES = monthnames()

# 1. DTO (Data Transfer Object)
@dataclass(frozen=True)
class ForecastDataDTO:
    """Carries strict, immutable data payload between the database layer and the Forecast logic."""

    incomes: list[int]
    expenses: list[int]
    savings: list[int]
    savings_close: list[int]
    planned_incomes: list[int]

    def to_dict(self) -> dict[str, list[int]]:
        """Converts DTO to dict for polars DataFrame compatibility."""
        return asdict(self)


class MonthlyDataFormatter:
    """Responsible ONLY for transforming database QuerySets into formatted lists."""

    @staticmethod
    def from_monthly_sum(data: QuerySet) -> list[int]:
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

    @staticmethod
    def from_planned_data(data: QuerySet, month_names: list | None = None) -> list[int]:
        """
        Calculates the total price for each month in a given dataset.

        Args:
            data (QuerySet): The dataset containing rows of monthly prices.

        Returns:
            list[int]: A list of total prices for each month,
            where the index represents the month (0-11).
            If the month does not exist in the dataset, the price will be 0.
        """
        month_names = month_names or MONTH_NAMES

        monthly_totals = [0] * 12
        month_map = {name: idx for idx, name in enumerate(month_names)}

        for month, price in it.chain.from_iterable(row.items() for row in data):
            if not price or month not in month_map:
                continue
            monthly_totals[month_map[month]] += price

        return monthly_totals


class ForecastDataProvider:
    """Coordinates the retrieval of data via services and maps them to a DTO."""

    def __init__(self, user: User):
        self.user = user
        self.year = cast(int, user.year)

    def get_forecast_data(self) -> ForecastDataDTO:
        incomes_qs = IncomeModelService(self.user).sum_by_month(self.year)
        expenses_qs = ExpenseModelService(self.user).sum_by_month(self.year)
        savings_qs = SavingModelService(self.user).sum_by_month(self.year)
        savings_close_qs = SavingCloseModelService(self.user).sum_by_month(self.year)

        planned_qs = (
            IncomePlanModelService(self.user).year(self.year).values(*MONTH_NAMES)
        )

        return ForecastDataDTO(
            incomes=MonthlyDataFormatter.from_monthly_sum(incomes_qs),
            expenses=MonthlyDataFormatter.from_monthly_sum(expenses_qs),
            savings=MonthlyDataFormatter.from_monthly_sum(savings_qs),
            savings_close=MonthlyDataFormatter.from_monthly_sum(savings_close_qs),
            planned_incomes=MonthlyDataFormatter.from_planned_data(planned_qs),
        )

    def get_beginning_balance(self) -> int:
        return (
            AccountBalanceModelService(self.user)
            .objects.filter(year=self.year)
            .aggregate(Sum("past", default=0))["past__sum"]
        )


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
    provider = ForecastDataProvider(user)
    month = get_month(year)

    # We pass the DTO as a dictionary since Forecast._create_df expects it
    forecast_data = provider.get_forecast_data().to_dict()
    forecast = Forecast(month, forecast_data).forecast()

    beginning = provider.get_beginning_balance()
    end = beginning + forecast

    return {
        "data": [beginning, end, forecast],
        "highlight": [False, False, True],
    }
