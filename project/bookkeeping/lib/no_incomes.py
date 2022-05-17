import json
from typing import Dict, List

from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from ...accounts.models import AccountBalance
from ...expenses.models import Expense, ExpenseType
from ...savings.models import Saving, SavingBalance


class NoIncomes():
    cut_sum = 0.0
    avg_expenses = 0.0
    savings = None
    unnecessary = []

    def __init__(self, journal, year):
        self._journal = journal
        self._year = year

        self._expenses = Expense.objects.last_months()

        account_sum = \
            AccountBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('balance'))['balance__sum']

        fund_sum = \
            SavingBalance.objects \
            .related() \
            .filter(year=year, saving_type__type__in=['shares', 'funds']) \
            .aggregate(Sum('market_value'))['market_value__sum']

        pension_sum = \
            SavingBalance.objects \
            .related() \
            .filter(year=year, saving_type__type='pensions') \
            .aggregate(Sum('market_value'))['market_value__sum']

        # convert decimal to float
        self._account_sum = float(account_sum) if account_sum else 0
        self._fund_sum = float(fund_sum) if fund_sum else 0
        self._pension_sum = float(pension_sum) if pension_sum else 0

        if journal.unnecessary_expenses:
            arr = json.loads(journal.unnecessary_expenses)
            self.unnecessary = list(
                ExpenseType
                .objects
                .related()
                .filter(pk__in=arr)
                .values_list("title", flat=True)
            )

        if journal.unnecessary_savings:
            self.unnecessary.append(_('Savings'))
            self.savings = Saving.objects.last_months()

        self._no_incomes_data()

    @property
    def summary(self) -> List[Dict[str, float]]:
        i1 = self._account_sum + self._fund_sum
        i2 = self._account_sum + self._fund_sum + self._pension_sum
        # cut_sum = 0 if not self.cut_sum else self.cut_sum

        return [{
            'label': 'money',
            'money_fund': i1,
            'money_fund_pension': i2
        }, {
            'label': 'no_cut',
            'money_fund': self._div(i1, self.avg_expenses),
            'money_fund_pension': self._div(i2, self.avg_expenses)
        }, {
            'label': 'cut',
            'money_fund': self._div(i1, (self.avg_expenses - self.cut_sum)),
            'money_fund_pension': self._div(i2, (self.avg_expenses - self.cut_sum))
        }]

    def _no_incomes_data(self):
        months = 6

        expenses_sum = 0.0
        cut_sum = 0.0
        for r in self._expenses:
            _sum = float(r['sum'])

            expenses_sum += _sum

            if r['title'] in self.unnecessary:
                cut_sum += _sum

        try:
            savings_sum = self.savings.get('sum', 0.0)
            savings_sum = float(savings_sum)
        except (AttributeError, TypeError):
            savings_sum = 0

        self.avg_expenses = (expenses_sum + savings_sum) / months
        self.cut_sum = (cut_sum + savings_sum) / months


    def _div(self, incomes: float, expenses: float) -> float:
        _val = 0.0

        if expenses:
            _val = incomes / expenses

        return _val
