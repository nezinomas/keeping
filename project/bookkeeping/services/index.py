import itertools as it
from dataclasses import dataclass, field

from django.db.models import F, Sum
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


@dataclass
class IndexServiceData:
    user: User
    year: int = field(init=False, default=1974)
    amount_start: int = field(init=False, default=0)
    data: list = field(init=False, default_factory=list)
    debts: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        self.year = self.user.year
        self.amount_start = self.get_amount_start()
        self.data = self.get_data()
        self.debts = self.get_debts()

    @property
    def columns(self) -> tuple:
        return (
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

    def get_amount_start(self) -> int:
        return (
            AccountBalanceModelService(self.user)
            .year(self.year)
            .aggregate(Sum("past"))["past__sum"]
            or 0
        )

    def get_data(self) -> list[dict]:
        return list(
            it.chain(
                IncomeModelService(self.user).sum_by_month(self.year),
                ExpenseModelService(self.user).sum_by_month(self.year),
                SavingModelService(self.user).sum_by_month(self.year),
                SavingCloseModelService(self.user).sum_by_month(self.year),
                self._get_debt("lend"),
                self._get_debt("borrow"),
                DebtReturnModelService(self.user, "lend").sum_by_month(self.year),
                DebtReturnModelService(self.user, "borrow").sum_by_month(self.year),
            )
        )

    def _get_debt(self, debt_type):
        return (
            DebtModelService(self.user, debt_type)
            .sum_by_month(self.year, closed=True)
            .values("date", "title", sum=F("sum_debt"))
        )

    def get_debts(self) -> dict:
        return {
            "lend": DebtModelService(self.user, "lend").sum_all(),
            "borrow": DebtModelService(self.user, "borrow").sum_all(),
        }


class IndexService:
    def __init__(self, balance: YearBalance, debts: dict = None):
        self._balance = balance
        self._debts = debts

    def balance_context(self):
        return {
            "data": self._balance.balance,
            "total_row": self._balance.total_row,
            "amount_end": self._balance.amount_end,
            "avg_row": self._balance.average,
        }

    def balance_short_context(self):
        start = self._balance.amount_start
        end = self._balance.amount_end

        return {
            "title": [
                _("Start of %(year)s") % ({"year": self._balance.year}),
                _("End of %(year)s") % ({"year": self._balance.year}),
                _("Balance"),
            ],
            "data": [start, end, (end - start)],
            "highlight": [False, False, True],
        }

    def chart_balance_context(self):
        return {
            "categories": [*month_names().values()],
            "incomes": self._balance.income_data,
            "incomes_title": _("Incomes"),
            "expenses": self._balance.expense_data,
            "expenses_title": _("Expenses"),
        }

    def averages_context(self):
        return {
            "title": [_("Average incomes"), _("Average expenses")],
            "data": [self._balance.avg_incomes, self._balance.avg_expenses],
        }

    def borrow_context(self):
        return self._generic_debt_context("borrow", "Borrow", "Borrow return")

    def lend_context(self):
        return self._generic_debt_context("lend", "Lend", "Lend return")

    def _generic_debt_context(self, debt_type, debt_str, debt_return_str):
        debt = self._debts.get(debt_type, {})
        if not debt.get("debt"):
            return {}

        return {
            "title": [_(debt_str), _(debt_return_str)],
            "data": [debt["debt"], debt["debt_return"]],
        }


def load_service(user):
    data = IndexServiceData(user)
    df = MakeDataFrame(user.year, data.data, data.columns)
    balance = YearBalance(data=df, amount_start=data.amount_start)
    return IndexService(balance=balance, debts=data.debts)
