import itertools as it
from dataclasses import dataclass, field

from django.db.models import Sum
from django.utils.translation import gettext as _

from ...accounts.models import AccountBalance
from ...core.lib.translation import month_names
from ...debts.models import Debt
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ...transactions.models import SavingClose
from ..lib.year_balance import YearBalance
from ..lib.make_dataframe import MakeDataFrame


@dataclass
class IndexServiceData:
    year: int
    amount_start: int = 0
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.amount_start = self.get_amount_start()
        self.data = self.get_data()

    @property
    def columns(self) -> tuple[str]:
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
            AccountBalance.objects.related()
            .filter(year=self.year)
            .aggregate(Sum("past"))["past__sum"]
            or 0
        )

    def get_data(self) -> list[dict]:
        qs_borrow = Debt.objects.sum_by_month(self.year, debt_type="borrow")
        qs_lend = Debt.objects.sum_by_month(self.year, debt_type="lend")

        return list(
            it.chain(
                Income.objects.sum_by_month(self.year),
                Expense.objects.sum_by_month(self.year),
                Saving.objects.sum_by_month(self.year),
                SavingClose.objects.sum_by_month(self.year),
                self.split_debt_data(qs_borrow),
                self.split_debt_data(qs_lend),
            )
        )

    def split_debt_data(self, data):
        final = []
        for row in data:
            date = row["date"]
            debt = {"date": date, "sum": row["sum_debt"], "title": row["title"]}
            debt_return = {
                "date": date,
                "sum": row["sum_return"],
                "title": f"{row['title']}_return",
            }
            final.extend((debt, debt_return))

        return final


class IndexService:
    def __init__(self, balance: YearBalance):
        self._balance = balance

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
            "title": [_("Start of year"), _("End of year"), _("Year balance")],
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
        if borrow := sum(self._balance.borrow_data):
            borrow_return = sum(self._balance.borrow_return_data)
            return {
                "title": [_("Borrow"), _("Borrow return")],
                "data": [borrow, borrow_return],
            }
        return {}

    def lend_context(self):
        if lend := sum(self._balance.lend_data):
            lend_return = sum(self._balance.lend_return_data)
            return {
                "title": [_("Lend"), _("Lend return")],
                "data": [lend, lend_return],
            }

        return {}


def load_service(year):
    data = IndexServiceData(year)
    df = MakeDataFrame(year, data.data, data.columns)
    balance = YearBalance(data=df, amount_start=data.amount_start)
    return IndexService(balance)
