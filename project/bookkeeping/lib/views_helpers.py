import itertools as it
from collections import Counter, defaultdict
from datetime import datetime
from typing import List

from django.db.models import Sum
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...accounts.models import AccountBalance
from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict as get_val
from ...core.lib.utils import sum_col
from ...debts.models import Debt
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import CalcDaySum
from ...savings.models import Saving
from ...transactions.models import SavingClose
from ..lib.day_spending import DaySpending
from ..lib.expense_summary import DayExpense, MonthExpense
from ..lib.year_balance import YearBalance


def expense_types(*args: str) -> List[str]:
    qs = (
        ExpenseType
        .objects
        .items()
        .values_list('title', flat=True)
    )

    arr = []
    [arr.append(x) for x in qs]
    [arr.append(x) for x in args]

    arr.sort()

    return arr


def necessary_expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType
        .objects
        .items()
        .filter(necessary=True)
        .values_list('title', flat=True)
    )

    list(qs.append(x) for x in args)

    qs.sort()

    return qs


def average(qs):
    now = datetime.now()
    arr = []

    for r in qs:
        year = r['year']
        sum_val = float(r['sum'])

        cnt = now.month if year == now.year else 12

        arr.append(sum_val / cnt)

    return arr


def add_latest_check_key(model, arr, year):
    items = model.objects.items(year)

    if items:
        for a in arr:
            latest = [x['latest_check'] for x in items if x.get('title') == a['title']]
            a['latest_check'] = latest[0] if latest else None


class MonthHelper():
    def __init__(self, request, year, month):
        self._request = request
        self._year = year
        self._month = month

        qs_expenses = Expense.objects.sum_by_day_ant_type(year, month)
        qs_savings = Saving.objects.sum_by_day(year, month)

        self._day = DayExpense(
            year=year,
            month=month,
            expenses=qs_expenses,
            **{_('Savings'): qs_savings}
        )

        self._day_plans = CalcDaySum(year)

        self._spending = DaySpending(
            year=year,
            month=month,
            month_df=self._day.expenses,
            exceptions=self._day.exceptions,
            necessary=necessary_expense_types(_('Savings')),
            plan_day_sum=get_val(self._day_plans.day_input, month),
            plan_free_sum=get_val(self._day_plans.expenses_free, month),
        )

        self._expenses_types = expense_types(_('Savings'))

    def render_chart_targets(self):
        targets = self._day_plans.targets(self._month, _('Savings'))
        (categories, data_target, data_fact) = self._day.chart_targets(
            self._expenses_types, targets)

        context = {
            'chart_targets_categories': categories,
            'chart_targets_data_target': data_target,
            'chart_targets_data_fact': data_fact,
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_targets.html',
            context=context,
            request=self._request
        )

    def render_chart_expenses(self):
        context = {
            'expenses': self._day.chart_expenses(self._expenses_types)
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_expenses.html',
            context=context,
            request=self._request
        )

    def render_info(self):
        fact_incomes = Income.objects.sum_by_month(self._year, self._month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_savings = self._day.total_row.get(_('Savings'))
        fact_savings = fact_savings if fact_savings else 0.0
        fact_expenses = self._day.total_row.get('total') - fact_savings
        fact_per_day = self._spending.avg_per_day
        fact_balance = fact_incomes - fact_expenses - fact_savings

        plan_incomes = get_val(self._day_plans.incomes, self._month)
        plan_savings = get_val(self._day_plans.savings, self._month)
        plan_expenses = plan_incomes - plan_savings
        plan_per_day = get_val(self._day_plans.day_input, self._month)
        plan_balance = get_val(self._day_plans.remains, self._month)

        items = [{
                'title': _('Incomes'),
                'plan': plan_incomes,
                'fact': fact_incomes,
                'delta': fact_incomes - plan_incomes,
            }, {
                'title': _('Expenses'),
                'plan': plan_expenses,
                'fact': fact_expenses,
                'delta': plan_expenses - fact_expenses,
            }, {
                'title': _('Savings'),
                'plan': plan_savings,
                'fact': fact_savings,
                'delta': plan_savings - fact_savings,
            }, {
                'title': _('Money for a day'),
                'plan': plan_per_day,
                'fact': fact_per_day,
                'delta': plan_per_day - fact_per_day,
            }, {
                'title': _('Balance'),
                'plan': plan_balance,
                'fact': fact_balance,
                'delta': fact_balance - plan_balance,
            },]

        return render_to_string(
            template_name='bookkeeping/includes/spending_info.html',
            context={'items': items},
            request=self._request
        )

    def render_month_table(self):
        context = {
            'expenses': it.zip_longest(self._day.balance, self._spending.spending),
            'total_row': self._day.total_row,
            'expense_types': self._expenses_types,
            'day': current_day(self._year, self._month, False),
        }

        return render_to_string(
            template_name='bookkeeping/includes/month_table.html',
            context=context,
            request=self._request
        )


class IndexHelper():
    def __init__(self, request, year):
        self._request = request
        self._year = year

        account_sum = \
            AccountBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('past'))['past__sum']
        account_sum = float(account_sum) if account_sum else 0.0

        self._YearBalance = YearBalance(
            year=year,
            data=self._collect_data(year),
            amount_start=account_sum)

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


class ExpensesHelper():
    def __init__(self, request, year):
        self._request = request
        self._year = year

        self._expense_types = expense_types()
        qs_expenses = Expense.objects.sum_by_month_and_type(year)

        self._MonthExpense = MonthExpense(
            year=year,
            expenses=qs_expenses,
            expenses_types=self._expense_types)

    def render_chart_expenses(self):
        context = {
            'data': self._MonthExpense.chart_data
        }
        return render_to_string(
            template_name='bookkeeping/includes/chart_expenses.html',
            context=context,
            request=self._request
        )

    def render_year_expenses(self):
        _expense_types = self._expense_types

        context = {
            'year': self._year,
            'data': self._MonthExpense.balance,
            'categories': _expense_types,
            'total_row': self._MonthExpense.total_row,
            'avg_row': self._MonthExpense.average,
        }
        return render_to_string(
            template_name='bookkeeping/includes/year_expenses.html',
            context=context,
            request=self._request
        )


class DetailedHelper():
    def __init__(self, year, *args, **kwargs):
        self._year = year

    def incomes_context(self, context):
        qs = Income.objects.sum_by_month_and_type(self._year)

        if not qs:
            return context

        return self._detailed_context(context, qs, _('Incomes'))

    def savings_context(self, context):
        qs = Saving.objects.sum_by_month_and_type(self._year)

        if not qs:
            return context

        return self._detailed_context(context, qs, _('Savings'))

    def expenses_context(self, context):
        qs = Expense.objects.sum_by_month_and_name(self._year)
        expenses_types = expense_types()

        for title in expenses_types:
            filtered = [*filter(lambda x: title in x['type_title'], qs)]

            if not filtered:
                continue

            self._detailed_context(
                context=context,
                data=filtered,
                name=_('Expenses / %(title)s') % ({'title': title})
            )

        return context

    def _detailed_context(self, context, data, name):
        context = context if context else {}

        if 'data' not in context.keys():
            context['data'] = []

        total_row = self._sum_detailed(data, 'date', ['sum'])
        total_col = self._sum_detailed(data, 'title', ['sum'])
        total = sum_col(total_col, 'sum')

        context['data'].append({
            'name': name,
            'data': data,
            'total_row': total_row,
            'total_col': total_col,
            'total': total,
        })

        return context

    def _sum_detailed(self, dataset, group_by_key, sum_value_keys):
        container = defaultdict(Counter)

        for item in dataset:
            key = item[group_by_key]
            values = {k: item[k] for k in sum_value_keys}
            container[key].update(values)

        new_dataset = []
        for item in container.items():
            new_dataset.append({group_by_key: item[0], **item[1]})

        new_dataset.sort(key=lambda item: item[group_by_key])

        return new_dataset
