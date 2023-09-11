import json
from typing import Dict, List

from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from ...accounts.models import AccountBalance
from ...expenses.models import Expense, ExpenseType
from ...savings.models import Saving, SavingBalance
from dataclasses import dataclass, field


@dataclass
class NoIncomesData:
    year: int
    months: int = field(default=6)
    unnecessary_expenses: list = field(default_factory=list)
    unnecessary_savings: bool = field(default=False)

    account_sum: float = field(init=False, default=0)
    fund_sum: float = field(init=False, default=0)
    pension_sum: float = field(init=False, default=0)

    expenses: list = field(init=False, default_factory=list)
    savings: dict = field(init=False, default_factory=dict)
    unnecessary: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.expenses = Expense.objects.last_months(months=self.months)
        self.account_sum = (
            AccountBalance.objects.related()
            .filter(year=self.year)
            .aggregate(Sum("balance"))["balance__sum"]
            or 0
        )

        self.fund_sum = (
            SavingBalance.objects.related()
            .filter(year=self.year, saving_type__type__in=["shares", "funds"])
            .aggregate(Sum("market_value"))["market_value__sum"]
            or 0
        )

        self.pension_sum = (
            SavingBalance.objects.related()
            .filter(year=self.year, saving_type__type="pensions")
            .aggregate(Sum("market_value"))["market_value__sum"]
            or 0
        )

        if self.unnecessary_expenses:
            arr = json.loads(self.unnecessary_expenses)
            self.unnecessary = list(
                ExpenseType.objects.related()
                .filter(pk__in=arr)
                .values_list("title", flat=True)
            )

        if self.unnecessary_savings:
            self.unnecessary.append(_("Savings"))
            self.savings = Saving.objects.last_months(months=self.months)


@dataclass
class NoIncomes:
    data: NoIncomesData
    cut_sum: float = field(init=False, default=0)
    avg_expenses: float = field(init=False, default=0)

    def __post_init__(self):
        self._calc()

    @property
    def unnecessary(self):
        return self.data.unnecessary

    @property
    def summary(self) -> List[Dict[str, float]]:
        i1 = self.data.account_sum + self.data.fund_sum
        i2 = i1 + self.data.pension_sum

        return [
            {   "label": "money",
                "money_fund": i1,
                "money_fund_pension": i2
            },
            {
                "label": "no_cut",
                "money_fund": self._div(i1, self.avg_expenses),
                "money_fund_pension": self._div(i2, self.avg_expenses),
            },
            {
                "label": "cut",
                "money_fund": self._div(i1, (self.avg_expenses - self.cut_sum)),
                "money_fund_pension": self._div(i2, (self.avg_expenses - self.cut_sum)),
            },
        ]

    def _calc(self):
        expenses_sum = 0
        cut_sum = 0
        for r in self.data.expenses:
            _sum = float(r["sum"])

            expenses_sum += _sum

            if r["title"] in self.data.unnecessary:
                cut_sum += _sum

        try:
            savings_sum = self.data.savings.get("sum", 0)
            savings_sum = float(savings_sum)
        except (AttributeError, TypeError):
            savings_sum = 0

        self.avg_expenses = (expenses_sum + savings_sum) / self.data.months
        self.cut_sum = (cut_sum + savings_sum) / self.data.months

    def _div(self, incomes: float, expenses: float) -> float:
        return incomes / expenses if expenses else 0
