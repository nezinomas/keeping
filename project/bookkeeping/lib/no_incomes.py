import json
from dataclasses import dataclass
from datetime import date

from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from ...accounts.services.model_services import AccountBalanceModelService
from ...core.mixins.shows_profit import FRESH_WORTH
from ...expenses.services.model_services import (
    ExpenseModelService,
    ExpenseTypeModelService,
)
from ...savings.services.model_services import (
    SavingBalanceModelService,
    SavingModelService,
)
from ...users.models import User


@dataclass(frozen=True)
class Data:
    account_sum: float
    fund_sum: float
    pension_sum: float
    expenses: list
    savings: dict
    unnecessary: list


class NoIncomes:
    def __init__(self, data: Data, months: int = 6):
        self.data = data
        self.months = months
        self.avg_expenses = 0.0
        self.cut_sum = 0.0
        self._calculate_monthly_metrics()

    @property
    def unnecessary(self) -> list:
        return self.data.unnecessary

    @property
    def summary(self) -> list[dict]:
        money_fund = self.data.account_sum + self.data.fund_sum
        money_fund_pension = money_fund + self.data.pension_sum
        reduced_expenses = self.avg_expenses - self.cut_sum

        return self._generate_dict(
            (f"{_('Money')}, €", money_fund, money_fund_pension, True),
            (
                _("No change in spending, month"),
                self._div(money_fund, self.avg_expenses),
                self._div(money_fund_pension, self.avg_expenses),
                False,
            ),
            (
                _("After spending cuts, month"),
                self._div(money_fund, reduced_expenses),
                self._div(money_fund_pension, reduced_expenses),
                False,
            ),
        )

    def _generate_dict(self, *entries) -> list[dict]:
        return [
            {
                "title": title,
                "money_fund": money_fund,
                "money_fund_pension": money_fund_pension,
                "price": is_currency,
            }
            for title, money_fund, money_fund_pension, is_currency in entries
        ]

    def _calculate_monthly_metrics(self):
        expenses_sum = 0
        cut_sum = 0

        for expense in self.data.expenses:
            val = expense.get("sum", 0)

            expenses_sum += val

            if expense.get("title") in self.data.unnecessary:
                cut_sum += val

        savings_val = self.data.savings.get("sum", 0)

        self.avg_expenses = (expenses_sum + savings_val) / self.months
        self.cut_sum = (cut_sum + savings_val) / self.months

    def _div(self, incomes: float, expenses: float) -> float:
        return incomes / expenses if expenses else 0.0


def load_service(user: User, year: int, today: date, months: int = 6) -> dict:
    unnecessary = _unnecessary_expense_titles(user)

    savings = {}
    if user.journal.unnecessary_savings:
        unnecessary.append(str(_("Savings")))
        savings = SavingModelService(user).spent_last_months(today, months)

    data = Data(
        account_sum=(
            AccountBalanceModelService(user)
            .year(year)
            .aggregate(Sum("balance", default=0))["balance__sum"]
        ),
        fund_sum=_fresh_worth(user, year, ["shares", "funds"]),
        pension_sum=_fresh_worth(user, year, ["pensions"]),
        expenses=list(ExpenseModelService(user).last_months(today, months)),
        savings=savings,
        unnecessary=unnecessary,
    )

    obj = NoIncomes(data, months=months)

    return {
        "no_incomes": obj.summary,
        "save_sum": obj.cut_sum,
        "not_use": obj.unnecessary,
        "avg_expenses": obj.avg_expenses,
    }


def _unnecessary_expense_titles(user: User) -> list[str]:
    ids = json.loads(user.journal.unnecessary_expenses or "[]")

    return list(
        ExpenseTypeModelService(user)
        .items()
        .filter(pk__in=ids)
        .values_list("title", flat=True)
    )


def _fresh_worth(user: User, year: int, types: list[str]) -> float:
    return (
        SavingBalanceModelService(user)
        .items()
        .filter(year=year, saving_type__type__in=types)
        .aggregate(worth=Sum("market_value", filter=FRESH_WORTH, default=0))["worth"]
    )
