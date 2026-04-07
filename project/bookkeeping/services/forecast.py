import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import cast

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


@dataclass(frozen=True)
class ForecastDataDTO:
    incomes: list[int]
    expenses: list[int]
    savings: list[int]
    savings_close: list[int]
    planned_incomes: list[int]


class MonthlyDataFormatter:
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

        for row in data:
            for idx, month in enumerate(month_names):
                if price := row.get(month):
                    monthly_totals[idx] += price

        return monthly_totals


class ForecastDataProvider:
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


@dataclass(frozen=True)
class AveragesDTO:
    expenses: float
    savings: float


@dataclass(frozen=True)
class CurrentMonthDTO:
    expenses: float
    savings: float
    incomes: float
    planned_incomes: float


class Forecast:
    def __init__(self, month: int, data: ForecastDataDTO):
        self._month = month
        self._data = data

        # Python lists are 0-indexed, so month 4 (April) means
        # slice up to index 3 for past data.
        self._past_idx = self._month - 1

    def balance(self) -> float:
        """Calculates balance from January to current month (excluding current month)."""
        incomes = sum(self._data.incomes[: self._past_idx])
        savings_close = sum(self._data.savings_close[: self._past_idx])
        expenses = sum(self._data.expenses[: self._past_idx])
        savings = sum(self._data.savings[: self._past_idx])

        return incomes + savings_close - expenses - savings

    def planned_incomes(self) -> float:
        """Calculates planned incomes from the next month to December."""
        # Slice from current month to the end
        return sum(self._data.planned_incomes[self._month :])

    def medians(self) -> AveragesDTO:
        """Calculates median expenses and savings for past months."""
        past_expenses = self._data.expenses[: self._past_idx]
        past_savings = self._data.savings[: self._past_idx]

        return AveragesDTO(
            expenses=statistics.median(past_expenses) if past_expenses else 0.0,
            savings=statistics.median(past_savings) if past_savings else 0.0,
        )

    def current_month(self) -> CurrentMonthDTO:
        """Retrieves expenses, savings, and incomes for the current month."""
        idx = self._past_idx
        return CurrentMonthDTO(
            expenses=float(self._data.expenses[idx]),
            savings=float(self._data.savings[idx]),
            incomes=float(self._data.incomes[idx]),
            planned_incomes=float(self._data.planned_incomes[idx]),
        )

    def forecast(self) -> float:
        """Calculates the forecasted balance for the end of the year."""
        avg = self.medians()
        current = self.current_month()
        months_left = 12 - self._month

        expenses = max(current.expenses, avg.expenses)
        savings = max(current.savings, avg.savings)
        incomes = max(current.incomes, current.planned_incomes)

        return (
            self.balance()
            + self.planned_incomes()
            + incomes
            - (expenses + avg.expenses * months_left)
            - (savings + avg.savings * months_left)
        )


def get_month(year: int) -> int:
    now = datetime.now()

    if year > now.year:
        return 1

    return 12 if year < now.year else now.month


def load_service(user: User) -> dict:
    year = cast(int, user.year)
    month = get_month(year)

    provider = ForecastDataProvider(user)
    forecast_data = provider.get_forecast_data()

    forecast = Forecast(month, forecast_data).forecast()

    beginning = provider.get_beginning_balance()
    end = beginning + forecast

    return {
        "data": [beginning, end, forecast],
        "highlight": [False, False, True],
    }
