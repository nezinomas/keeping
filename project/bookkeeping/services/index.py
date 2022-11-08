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


@dataclass
class IndexServiceData:
    year: int
    amount_start: float = 0.0
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.amount_start = self.get_amount_start()
        self.data = self.get_data()

    def get_amount_start(self):
        _sum = \
            AccountBalance.objects \
            .related() \
            .filter(year=self.year) \
            .aggregate(Sum('past'))['past__sum'] or 0.0

        return float(_sum)

    def get_data(self) -> list[dict]:
        qs_borrow = \
            Debt.objects \
            .sum_by_month(self.year, debt_type='borrow')
        qs_lend = \
            Debt.objects \
            .sum_by_month(self.year, debt_type='lend')

        # generate debts and debts_return arrays
        borrow, borrow_return = self.get_debt_data(qs_borrow)
        lend, lend_return = self.get_debt_data(qs_lend)

        return {
            'incomes': Income.objects.sum_by_month(self.year),
            'expenses': Expense.objects.sum_by_month(self.year),
            'savings': Saving.objects.sum_by_month(self.year),
            'savings_close': SavingClose.objects.sum_by_month(self.year),
            'borrow': borrow,
            'borrow_return': borrow_return,
            'lend': lend,
            'lend_return': lend_return,
        }

    def get_debt_data(self, data):
        debt, debt_return = [], []

        for row in data:
            date = row['date']
            debt.append(
                {'date': date, 'sum': row['sum_debt']})
            debt_return.append(
                {'date': date, 'sum': row['sum_return']})

        return debt, debt_return


class IndexService():
    def __init__(self, balance: YearBalance):
        self._balance = balance

    def balance_context(self):
        return {
            'data': self._balance.balance,
            'total_row': self._balance.total_row,
            'amount_end': self._balance.amount_end,
            'avg_row': self._balance.average,
        }

    def balance_short_context(self):
        start = self._balance.amount_start
        end = self._balance.amount_end

        return {
            'title': [_('Start of year'), _('End of year'), _('Year balance')],
            'data': [start, end, (end - start)],
            'highlight': [False, False, True],
        }

    def chart_balance_context(self):
        return {
            'categories': [*month_names().values()],
            'incomes': self._balance.income_data,
            'incomes_title': _('Incomes'),
            'expenses': self._balance.expense_data,
            'expenses_title': _('Expenses'),
        }

    def averages_context(self):
        return {
            'title': [_('Average incomes'), _('Average expenses')],
            'data': [self._balance.avg_incomes, self._balance.avg_expenses],
        }

    def borrow_context(self):
        if borrow := sum(self._balance.borrow_data):
            borrow_return = sum(self._balance.borrow_return_data)
            return {
                'title': [_('Borrow'), _('Borrow return')],
                'data': [borrow, borrow_return],
            }
        return {}

    def lend_context(self):
        if lend := sum(self._balance.lend_data):
            lend_return = sum(self._balance.lend_return_data)
            return {
                'title': [_('Lend'), _('Lend return')],
                'data': [lend, lend_return],
            }

        return {}

    @staticmethod
    def percentage_from_incomes(incomes, savings):
        return \
            (savings * 100) / incomes \
            if incomes and savings else 0
