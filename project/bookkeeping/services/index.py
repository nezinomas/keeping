import itertools as it
from dataclasses import dataclass

from django.db.models import F, QuerySet, Sum
from django.utils.translation import gettext as _

from ...accounts.services.model_services import AccountBalanceModelService
from ...core.lib.translation import month_names
from ...debts.services.model_services import DebtModelService, DebtReturnModelService
from ...expenses.services.model_services import ExpenseModelService
from ...incomes.services.model_services import IncomeModelService
from ...savings.services.model_services import SavingModelService
from ...transactions.services.model_services import SavingCloseModelService
from ...users.models import User
from ..lib.make_dataframe import MakeDataFrame
from ..lib.year_balance import YearBalance

INDEX_COLUMNS = (
    "incomes",
    "expenses",
    "savings",
    "savings_close",
    "borrow",
    "borrow_return",
    "lend",
    "lend_return",
    "balance",
    "money_flow",
)


@dataclass(frozen=True)
class IndexDataDTO:
    amount_start: int
    monthly_data: list[dict]
    debts: dict[str, dict]


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


class IndexContextBuilder:
    def __init__(self, balance: YearBalance, debts: dict | None = None):
        self._balance = balance
        self._debts = debts or {}

    def balance_context(self) -> dict:
        return {
            "data": self._balance.balance,
            "total_row": self._balance.total_row,
            "amount_end": self._balance.amount_end,
            "avg_row": self._balance.average,
        }

    def balance_short_context(self) -> dict:
        start = self._balance.amount_start
        end = self._balance.amount_end

        return {
            "title": [
                _("Start of %(year)s") % {"year": self._balance.year},
                _("End of %(year)s") % {"year": self._balance.year},
                _("Balance"),
            ],
            "data": [start, end, (end - start)],
            "highlight": [False, False, True],
        }

    def chart_balance_context(self) -> dict:
        return {
            "categories": list(month_names().values()),
            "incomes": self._balance.income_data,
            "incomes_title": _("Incomes"),
            "expenses": self._balance.expense_data,
            "expenses_title": _("Expenses"),
        }

    def averages_context(self) -> dict:
        return {
            "title": [_("Average incomes"), _("Average expenses")],
            "data": [self._balance.avg_incomes, self._balance.avg_expenses],
        }

    def borrow_context(self) -> dict:
        return self._generic_debt_context("borrow", "Borrow", "Borrow return")

    def lend_context(self) -> dict:
        return self._generic_debt_context("lend", "Lend", "Lend return")

    def _generic_debt_context(
        self, debt_type: str, debt_str: str, debt_return_str: str
    ) -> dict:
        debt = self._debts.get(debt_type, {})
        if not debt.get("debt"):
            return {}

        return {
            "title": [_(debt_str), _(debt_return_str)],
            "data": [debt["debt"], debt["debt_return"]],
        }


# 5. Orchestrator
def load_service(user: User) -> IndexContextBuilder:
    year = user.year
    provider = IndexDataProvider(user)
    dto = provider.get_data()

    df = MakeDataFrame(year, dto.monthly_data, INDEX_COLUMNS)
    balance = YearBalance(data=df, amount_start=dto.amount_start)

    return IndexContextBuilder(balance=balance, debts=dto.debts)
