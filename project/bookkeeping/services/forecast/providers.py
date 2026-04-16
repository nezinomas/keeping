from typing import cast

from django.db.models import QuerySet, Sum

from ....accounts.services.model_services import AccountBalanceModelService
from ....expenses.services.model_services import ExpenseModelService
from ....incomes.services.model_services import IncomeModelService
from ....plans.services.model_services import IncomePlanModelService
from ....savings.services.model_services import SavingModelService
from ....transactions.services.model_services import SavingCloseModelService
from ....users.models import User
from .dtos import ForecastDataDTO


class MonthlyDataFormatter:
    @staticmethod
    def from_monthly_sum(data: QuerySet) -> list[int]:
        arr = [0] * 12
        for row in data:
            if date := row.get("date"):
                arr[date.month - 1] = row.get("sum")
        return arr

    @staticmethod
    def from_planned_data(data: QuerySet, month_names: list | None = None) -> list[int]:
        arr = [0] * 12
        for row in data:
            if month := row.get("month"):
                arr[month - 1] = row.get("price")
        return arr


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
            IncomePlanModelService(self.user).year(self.year).values("month", "price")
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