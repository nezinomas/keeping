from django.db.models import Sum

from ....expenses.services.model_services import (
    ExpenseModelService,
    ExpenseTypeModelService,
)
from ....incomes.services.model_services import IncomeModelService
from ....plans.lib.calc_day_sum import PlanCollectData
from ....plans.services.model_services import PlanAggregatorService
from ....savings.services.model_services import SavingModelService
from ....users.models import User
from .dtos import MonthDataDTO


class MonthDataProvider:
    def __init__(self, user: User):
        self.user = user
        self.year = user.year
        self.month = user.month

    def get_data(self) -> MonthDataDTO:
        return MonthDataDTO(
            incomes=self._get_incomes(),
            expenses=list(
                ExpenseModelService(self.user).sum_by_day_and_type(
                    self.year, self.month
                )
            ),
            expense_types=list(
                ExpenseTypeModelService(self.user).objects.values_list(
                    "title", flat=True
                )
            ),
            necessary_expense_types=list(
                ExpenseTypeModelService(self.user)
                .objects.filter(necessary=True)
                .values_list("title", flat=True)
            ),
            savings=list(
                SavingModelService(self.user).sum_by_day(self.year, self.month)
            ),
            plans_data=PlanCollectData(self.user, self.year).get_data(),
            targets=PlanAggregatorService(self.user).get_monthly_plan_targets(
                self.year, self.month
            ),
        )

    def _get_incomes(self) -> int:
        return (
            IncomeModelService(self.user)
            .objects.filter(date__year=self.year, date__month=self.month)
            .aggregate(Sum("price", default=0))["price__sum"]
        )
