from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _

from ....core.lib.money_cells import amount, percent
from ....core.lib.stat_card import Card, EmptyStatCard, StatCard
from ....core.lib.translation import month_names
from ....debts.models import Debt
from ....debts.services.model_services import DebtModelService
from ....users.models import User
from ...lib.make_dataframe import MakeDataFrame
from ...lib.year_balance import YearBalance
from ..wealth.presenters import WealthPresenter
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


def cash_flow_check(cash_flow: int, accounts_balance: int) -> str:
    state = ""
    if cash_flow != accounts_balance:
        state = "mismatch"
    return state


class IndexContextBuilder:
    def __init__(self, balance: YearBalance):
        self._balance = balance

    def balance_context(self, accounts_balance: int) -> dict:
        return {
            "data": self._balance.balance,
            "total_row": self._balance.total_row,
            "amount_end": self._balance.amount_end,
            "avg_row": self._balance.average,
            "cash_flow_check": self.check_cash_flow(accounts_balance),
        }

    def check_cash_flow(self, accounts_balance: int) -> str:
        return cash_flow_check(self._balance.amount_end, accounts_balance)

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

    def cards(self, wealth: WealthPresenter) -> list[Card]:
        averages = {
            _("Average incomes"): self._balance.avg_incomes,
            _("Average expenses"): self._balance.avg_expenses,
        }
        cards = [
            StatCard(_("Money"), value=amount(wealth.money)),
            StatCard(_("Wealth"), value=amount(wealth.wealth)),
        ]

        if self._balance.is_coming:
            return cards + [EmptyStatCard(title) for title in averages]

        return cards + [
            StatCard(title, value=amount(figure)) for title, figure in averages.items()
        ]


def _profit_card(title: str, table: dict) -> Card:
    """A table's total profit, empty when there is none (no rows, or no gain)."""
    total = table["total_row"]
    if not total["profit_sum"]:
        return EmptyStatCard(title)

    return StatCard(
        title,
        value=amount(total["profit_sum"]),
        note=f"{percent(total['profit_proc'])}%",
    )


def funds_cards(savings: dict, pensions: dict) -> list[Card]:
    """Fondai's Cards: the Saved share, then each table's total profit."""
    return [
        savings["saved_share"],
        _profit_card(_("Fund profit"), savings),
        _profit_card(_("Pension profit"), pensions),
    ]


def load_service(user: User, today: date) -> IndexContextBuilder:
    year = user.selected_year()
    provider = IndexDataProvider(user)
    dto = provider.get_data()

    df = MakeDataFrame.for_year(year, dto.monthly_data, INDEX_COLUMNS)
    balance = YearBalance(data=df, amount_start=dto.amount_start, today=today)

    return IndexContextBuilder(balance=balance)


@dataclass(frozen=True)
class IncomesExpensesChart:
    """Grafikai's incomes-against-expenses chart, month by month."""

    incomes: list[int]
    expenses: list[int]

    @classmethod
    def load(cls, user: User) -> "IncomesExpensesChart":
        provider = IndexDataProvider(user)
        data = provider.get_incomes_and_expenses()
        df = MakeDataFrame.for_year(provider.year, data, ("incomes", "expenses")).data
        return cls(df["incomes"].to_list(), df["expenses"].to_list())

    def context(self) -> dict:
        return {
            "categories": list(month_names().values()),
            "incomes": self.incomes,
            "incomes_title": _("Incomes"),
            "expenses": self.expenses,
            "expenses_title": _("Expenses"),
        }


@dataclass(frozen=True)
class DebtsTable:
    """Apžvalga's Debts table: what is owed and what came back, whatever its year."""

    debts: dict[Debt.DebtType, dict]

    @classmethod
    def load(cls, user: User) -> "DebtsTable":
        return cls(
            {
                debt_type: DebtModelService(user, debt_type).sum_all()
                for debt_type in Debt.DebtType
            }
        )

    def debts_context(self) -> list[dict]:
        """A row per kind with a debt, Lend first, as Debts' own tabs."""
        rows = []
        for debt_type in (Debt.DebtType.LEND, Debt.DebtType.BORROW):
            sums = self.debts[debt_type]
            if not sums["debt"]:
                continue
            rows.append(
                {
                    "title": debt_type.label,
                    "debt": sums["debt"],
                    "debt_return": sums["debt_return"],
                    "remaining": sums["debt"] - sums["debt_return"],
                }
            )
        return rows
