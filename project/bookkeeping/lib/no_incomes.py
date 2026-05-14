import json
from dataclasses import dataclass
from typing import Dict, List, Union

from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from ...accounts.services.model_services import AccountBalanceModelService
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
    savings: Union[dict, None]
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
    def summary(self) -> List[Dict]:
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

    def _generate_dict(self, *entries) -> List[Dict]:
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

        savings_val = self.data.savings.get("sum", 0) if self.data.savings else 0

        self.avg_expenses = (expenses_sum + savings_val) / self.months
        self.cut_sum = (cut_sum + savings_val) / self.months

    def _div(self, incomes: float, expenses: float) -> float:
        return incomes / expenses if expenses else 0


def load_service(user: User, year: int, months: int = 6) -> dict:

    # 1. Fetch Unnecessary Titles
    unnecessary_ids = (
        json.loads(user.journal.unnecessary_expenses)
        if user.journal.unnecessary_expenses
        else []
    )
    unnecessary_titles = list(
        ExpenseTypeModelService(user)
        .items()
        .filter(pk__in=unnecessary_ids)
        .values_list("title", flat=True)
    )

    # 2. Fetch Savings
    savings_data = {}
    if user.journal.unnecessary_savings:
        unnecessary_titles.append(str(_("Savings")))
        savings_data = SavingModelService(user).last_months(months=months)

    # 3. Build Pure Data Object
    data_payload = Data(
        account_sum=(
            AccountBalanceModelService(user)
            .year(year)
            .aggregate(Sum("balance", default=0))["balance__sum"]
        ),
        fund_sum=(
            SavingBalanceModelService(user)
            .items()
            .filter(year=year, saving_type__type__in=["shares", "funds"])
            .aggregate(Sum("market_value", default=0))["market_value__sum"]
        ),
        pension_sum=(
            SavingBalanceModelService(user)
            .items()
            .filter(year=year, saving_type__type="pensions")
            .aggregate(Sum("market_value", default=0))["market_value__sum"]
        ),
        expenses=list(ExpenseModelService(user).last_months(months=months)),
        savings=savings_data,
        unnecessary=unnecessary_titles,
    )

    obj = NoIncomes(data_payload, months=months)

    return {
        "no_incomes": obj.summary,
        "save_sum": obj.cut_sum,
        "not_use": obj.unnecessary,
        "avg_expenses": obj.avg_expenses,
    }
