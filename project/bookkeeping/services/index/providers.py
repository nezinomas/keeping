import itertools as it

from django.db.models import F, QuerySet, Sum
from django.utils.translation import gettext as _

from ....accounts.services.model_services import AccountBalanceModelService
from ....debts.services.model_services import DebtModelService, DebtReturnModelService
from ....expenses.services.model_services import ExpenseModelService
from ....incomes.services.model_services import IncomeModelService
from ....savings.services.model_services import SavingModelService
from ....transactions.services.model_services import SavingCloseModelService
from ....users.models import User
from .dtos import IndexDataDTO


class IndexDataProvider:
    def __init__(self, user: User):
        self.user = user
        self.year = user.year

    def get_data(self) -> IndexDataDTO:
        return IndexDataDTO(
            amount_start=self._get_amount_start(),
            monthly_data=self._get_monthly_data(),
            debts=self._get_debts(),
        )

    def _get_amount_start(self) -> int:
        return (
            AccountBalanceModelService(self.user)
            .year(self.year)
            .aggregate(Sum("past"))["past__sum"]
            or 0
        )

    def _get_monthly_data(self) -> list[dict]:
        return list(
            it.chain(
                IncomeModelService(self.user).sum_by_month(self.year),
                ExpenseModelService(self.user).sum_by_month(self.year),
                SavingModelService(self.user).sum_by_month(self.year),
                SavingCloseModelService(self.user).sum_by_month(self.year),
                self._get_debt_monthly("lend"),
                self._get_debt_monthly("borrow"),
                DebtReturnModelService(self.user, "lend").sum_by_month(self.year),
                DebtReturnModelService(self.user, "borrow").sum_by_month(self.year),
            )
        )

    def _get_debt_monthly(self, debt_type: str) -> QuerySet:
        return (
            DebtModelService(self.user, debt_type)
            .sum_by_month(self.year, closed=True)
            .values("date", "title", sum=F("sum_debt"))
        )

    def _get_debts(self) -> dict[str, dict]:
        return {
            "lend": DebtModelService(self.user, "lend").sum_all(),
            "borrow": DebtModelService(self.user, "borrow").sum_all(),
        }