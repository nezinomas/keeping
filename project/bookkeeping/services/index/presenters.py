from datetime import date

from django.utils.translation import gettext as _

from ....core.lib.translation import month_names
from ....debts.models import Debt
from ....users.models import User
from ...lib.make_dataframe import MakeDataFrame
from ...lib.year_balance import YearBalance
from .providers import IndexDataProvider

INDEX_COLUMNS = (
    "incomes",
    "expenses",
    "savings",
    "savings_close",
    "savings_account_fee",
    "borrow",
    "borrow_return",
    "lend",
    "lend_return",
    "balance",
    "money_flow",
)


class IndexContextBuilder:
    def __init__(self, balance: YearBalance, debts: dict[Debt.DebtType, dict]):
        self._balance = balance
        self._debts = debts

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
        return self._generic_debt_context(
            Debt.DebtType.BORROW, _("Borrow"), _("Borrow return")
        )

    def lend_context(self) -> dict:
        return self._generic_debt_context(
            Debt.DebtType.LEND, _("Lend"), _("Lend return")
        )

    def _generic_debt_context(
        self, debt_type: Debt.DebtType, debt_title: str, return_title: str
    ) -> dict:
        debt = self._debts[debt_type]
        if not debt["debt"]:
            return {}

        return {
            "title": [debt_title, return_title],
            "data": [debt["debt"], debt["debt_return"]],
        }


def load_service(user: User, today: date) -> IndexContextBuilder:
    year = user.year
    provider = IndexDataProvider(user)
    dto = provider.get_data()

    df = MakeDataFrame.for_year(year, dto.monthly_data, INDEX_COLUMNS)
    balance = YearBalance(data=df, amount_start=dto.amount_start, today=today)

    return IndexContextBuilder(balance=balance, debts=dto.debts)
