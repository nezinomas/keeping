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


class IndexServiceData:
    @staticmethod
    def amount_start(year):
        _sum = \
            AccountBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('past'))['past__sum']

        return float(_sum) if _sum else 0.0

    @staticmethod
    def data(year: int) -> list[dict]:
        qs_borrow = Debt.objects.sum_by_month(year, debt_type='borrow')
        qs_lend = Debt.objects.sum_by_month(year, debt_type='lend')

        # generate debts and debts_return arrays
        borrow, borrow_return, lend, lend_return = [], [], [], []
        for x in qs_borrow:
            borrow.append({'date': x['date'], 'sum': x['sum_debt']})
            borrow_return.append({'date': x['date'], 'sum': x['sum_return']})

        for x in qs_lend:
            lend.append({'date': x['date'], 'sum': x['sum_debt']})
            lend_return.append({'date': x['date'], 'sum': x['sum_return']})

        return {
            'incomes': Income.objects.sum_by_month(year),
            'expenses': Expense.objects.sum_by_month(year),
            'savings': Saving.objects.sum_by_month(year),
            'savings_close': SavingClose.objects.sum_by_month(year),
            'borrow': borrow,
            'borrow_return': borrow_return,
            'lend': lend,
            'lend_return': lend_return,
        }


class IndexService():
    def __init__(self, balance: YearBalance):
        self._YearBalance = balance

    def balance_context(self):
        return {
            'data': self._YearBalance.balance,
            'total_row': self._YearBalance.total_row,
            'amount_end': self._YearBalance.amount_end,
            'avg_row': self._YearBalance.average,
        }

    def balance_short_context(self):
        start = self._YearBalance.amount_start
        end = self._YearBalance.amount_end
        print(f'{start=} {end=}')
        return {
            'title': [_('Start of year'), _('End of year'), _('Year balance')],
            'data': [start, end, (end - start)],
            'highlight': [False, False, True],
        }

    def chart_balance_context(self):
        return {
            'categories': [*month_names().values()],
            'incomes': self._YearBalance.income_data,
            'incomes_title': _('Incomes'),
            'expenses': self._YearBalance.expense_data,
            'expenses_title': _('Expenses'),
        }

    def averages_context(self):
        return {
            'title': [_('Average incomes'), _('Average expenses')],
            'data': [self._YearBalance.avg_incomes, self._YearBalance.avg_expenses],
        }

    def borrow_context(self):
        if borrow := sum(self._YearBalance.borrow_data):
            borrow_return = sum(self._YearBalance.borrow_return_data)
            return {
                'title': [_('Borrow'), _('Borrow return')],
                'data': [borrow, borrow_return],
            }
        return {}

    def lend_context(self):
        if lend := sum(self._YearBalance.lend_data):
            lend_return = sum(self._YearBalance.lend_return_data)
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
