from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...accounts.models import AccountBalance
from ...debts.models import Debt
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ...transactions.models import SavingClose
from .year_balance import YearBalance


class IndexHelper():
    def __init__(self, request, year):
        self._request = request
        self._year = year

        account_sum = \
            AccountBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('past')) \
            ['past__sum']
        account_sum = float(account_sum) if account_sum else 0.0

        self._YearBalance = YearBalance(
            year=year,
            data=self._collect_data(year),
            amount_start=account_sum
        )

    def _collect_data(self, year):
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

        data = {
            'incomes': Income.objects.sum_by_month(year),
            'expenses': Expense.objects.sum_by_month(year),
            'savings': Saving.objects.sum_by_month(year),
            'savings_close': SavingClose.objects.sum_by_month(year),
            'borrow': borrow,
            'borrow_return': borrow_return,
            'lend': lend,
            'lend_return': lend_return,
        }

        return data

    def render_year_balance(self):
        context = {
            'year': self._year,
            'data': self._YearBalance.balance,
            'total_row': self._YearBalance.total_row,
            'amount_end': self._YearBalance.amount_end,
            'avg_row': self._YearBalance.average,
        }

        return render_to_string(
            template_name='bookkeeping/includes/year_balance.html',
            context=context,
            request=self._request
        )

    def render_year_balance_short(self):
        start = self._YearBalance.amount_start
        end = self._YearBalance.amount_end
        context = {
            'title': [_('Start of year'), _('End of year'), _('Year balance')],
            'data': [start, end, (end - start)],
            'highlight': [False, False, True],
        }
        return context

    def render_chart_balance(self):
        context = {
            'e': self._YearBalance.expense_data,
            'i': self._YearBalance.income_data,
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_balance.html',
            context=context,
            request=self._request
        )

    def render_averages(self):
        context = {
            'title': [_('Average incomes'), _('Average expenses')],
            'data': [self._YearBalance.avg_incomes, self._YearBalance.avg_expenses],
        }
        return context

    def render_borrow(self):
        borrow = sum(self._YearBalance.borrow_data)
        borrow_return = sum(self._YearBalance.borrow_return_data)

        if borrow:
            context = {
                'title': [_('Borrow'), _('Borrow return')],
                'data': [borrow, borrow_return],
            }
            return context

        return {}

    def render_lend(self):
        lend = sum(self._YearBalance.lend_data)
        lend_return = sum(self._YearBalance.lend_return_data)

        if lend:
            context = {
                'title': [_('Lend'), _('Lend return')],
                'data': [lend, lend_return],
            }
            return context

        return {}

    @staticmethod
    def percentage_from_incomes(incomes, savings):
        if incomes and savings:
            return (savings * 100) / incomes

        return 0
