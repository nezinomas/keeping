import itertools as it
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import List

from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...accounts.models import AccountBalance
from ...bookkeeping.models import AccountWorth, PensionWorth, SavingWorth
from ...core.lib import utils
from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict as get_val
from ...core.lib.utils import sum_all, sum_col
from ...debts.models import Borrow, BorrowReturn, Lent, LentReturn
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...pensions.models import PensionBalance
from ...plans.lib.calc_day_sum import CalcDaySum
from ...savings.models import Saving, SavingBalance
from ...transactions.models import SavingClose
from ..lib.day_spending import DaySpending
from ..lib.expense_summary import DayExpense, MonthExpense
from ..lib.no_incomes import NoIncomes
from ..lib.year_balance import YearBalance


def expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType
        .objects
        .items()
        .values_list('title', flat=True)
    )

    list(qs.append(x) for x in args)

    qs.sort()

    return qs


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


def sum_detailed(dataset, group_by_key, sum_value_keys):
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


def average(qs):
    now = datetime.now()
    arr = []

    for r in qs:
        year = r['year']
        sum_val = float(r['sum'])

        cnt = now.month if year == now.year else 12

        arr.append(sum_val / cnt)

    return arr


def add_latest_check_key(model, arr):
    items = model.objects.items()
    for a in arr:
        latest = [x['latest_check']
                    for x in items if x.get('title') == a['title']]
        a['latest_check'] = latest[0] if latest else None


# ---------------------------------------------------------------------------------------
#                                                                             No Incomes
# --------------------------------------------------------------------------------------
def no_incomes_data(expenses, savings=None, not_use=None):
    months = 6
    not_use = not_use if not_use else []

    expenses_sum = 0.0
    cut_sum = 0.0
    for r in expenses:
        _sum = float(r['sum'])

        expenses_sum += _sum

        if r['title'] in not_use:
            cut_sum += _sum

    savings_sum = savings['sum'] if savings else 0
    savings_sum = float(savings_sum) if savings_sum else 0.0

    expenses_avg = (expenses_sum + savings_sum) / months
    cut_avg = (cut_sum + savings_sum) / months

    return expenses_avg, cut_avg


def month_context(request, context=None):
    context = context if context else {}
    year = request.user.year
    month = request.user.month

    obj = MonthHelper(request, year, month)

    context.update({
        'month_table': obj.render_month_table(),
        'info': obj.render_info(),
        'chart_expenses': obj.render_chart_expenses(),
        'chart_targets': obj.render_chart_targets(),
    })
    return context


def detailed_context(context, data, name):
    if not 'data' in context.keys():
        context['data'] = []

    total_row = sum_detailed(data, 'date', ['sum'])
    total_col = sum_detailed(data, 'title', ['sum'])
    total = sum_col(total_col, 'sum')

    context['data'].append({
        'name': name,
        'data': data,
        'total_row': total_row,
        'total_col': total_col,
        'total': total,
    })


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
        fact_expenses = self._day.total_row.get('total')
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_expenses = self._day.total

        plan_incomes = get_val(self._day_plans.incomes, self._month)
        plan_expenses = plan_incomes
        plan_day_sum = get_val(self._day_plans.day_input, self._month)
        plan_remains = get_val(self._day_plans.remains, self._month)

        context = {
            'plan_per_day': plan_day_sum,
            'plan_incomes': plan_incomes,
            'plan_expenses': plan_expenses,
            'plan_remains': plan_remains,
            'fact_per_day': self._spending.avg_per_day,
            'fact_incomes': fact_incomes,
            'fact_expenses': fact_expenses,
            'fact_remains': fact_incomes - fact_expenses,
        }

        return render_to_string(
            template_name='bookkeeping/includes/spending_info.html',
            context=context,
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

        self._account = [*AccountBalance.objects.year(year)]
        self._fund = [*SavingBalance.objects.year(year)]
        self._pension = [*PensionBalance.objects.year(year)]

        qs_income = Income.objects.sum_by_month(year)
        qs_savings = Saving.objects.sum_by_month(year)
        qs_savings_close = SavingClose.objects.sum_by_month(year)
        qs_borrow = Borrow.objects.sum_by_month(year)
        qs_borrow_return = BorrowReturn.objects.sum_by_month(year)
        qs_lent = Lent.objects.sum_by_month(year)
        qs_lent_return = LentReturn.objects.sum_by_month(year)
        qs_expenses = Expense.objects.sum_by_month(year)

        self._YearBalance = YearBalance(
            year=year,
            incomes=qs_income,
            expenses=qs_expenses,
            savings=qs_savings,
            savings_close=qs_savings_close,
            borrow=qs_borrow,
            borrow_return=qs_borrow_return,
            lent=qs_lent,
            lent_return=qs_lent_return,
            amount_start=sum_col(self._account, 'past'))

    def render_year_balance(self):
        context = {
            'year': self._year,
            'data': self._YearBalance.balance,
            'total_row': self._YearBalance.total_row,
            'avg_row': self._YearBalance.average,
            'accounts_amount_end': sum_col(self._account, 'balance'),
            'months_amount_end': self._YearBalance.amount_end,
        }
        return render_to_string(
            'bookkeeping/includes/year_balance.html',
            context,
            self._request
        )

    def render_year_balance_short(self):
        start = self._YearBalance.amount_start
        end = self._YearBalance.amount_end
        context = {
            'title': [_('Start of year'), _('End of year'), _('Year balance')],
            'data': [start, end, (end - start)],
            'highlight': [False, False, True],
        }
        return self._render_info_table(context)

    def render_chart_balance(self):
        context = {
            'e': self._YearBalance.expense_data,
            'i': self._YearBalance.income_data,
        }

        return render_to_string(
            'bookkeeping/includes/chart_balance.html',
            context,
            self._request
        )

    def render_accounts(self):
        # add latest_check date to accounts dictionary
        add_latest_check_key(AccountWorth, self._account)

        context = {
            'accounts': self._account,
            'total_row': sum_all(self._account),
            'accounts_amount_end': sum_col(self._account, 'balance'),
            'months_amount_end': self._YearBalance.amount_end,
        }
        return render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            context,
            self._request
        )

    def render_savings(self):
        funds = self._fund
        incomes = self._YearBalance.total_row.get('incomes')
        savings = self._YearBalance.total_row.get('savings')
        context = IndexHelper.savings_context(funds, incomes, savings)

        return render_to_string(
            'bookkeeping/includes/worth_table.html',
            context,
            self._request
        )

    @staticmethod
    def savings_context(funds, incomes, savings):
        total_row = sum_all(funds)

        if not total_row.get('invested'):
            return ''

        # add latest_check date to savibgs dictionary
        add_latest_check_key(SavingWorth, funds)

        context = {
            'title': _('Funds'),
            'items': funds,
            'total_row': total_row,
            'percentage_from_incomes': (
                IndexHelper.percentage_from_incomes(incomes, savings)
            ),
            'profit_incomes_proc': (
                IndexHelper.percentage_from_incomes(
                    total_row.get('incomes'),
                    total_row.get('market_value')
                ) - 100
            ),
            'profit_invested_proc': (
                IndexHelper.percentage_from_incomes(
                    total_row.get('invested'),
                    total_row.get('market_value')
                ) - 100
            ),
        }
        return context

    def render_pensions(self):
        context = IndexHelper.pensions_context(self._pension)

        return render_to_string(
            'bookkeeping/includes/worth_table.html',
            context,
            self._request
        )

    @staticmethod
    def pensions_context(pensions):
        total_row = sum_all(pensions)
        if not total_row.get('invested'):
            return ''

        # add latest_check date to pensions dictionary
        add_latest_check_key(PensionWorth, pensions)

        context = {
            'title': _('Pensions'),
            'items': pensions,
            'total_row': sum_all(pensions),
        }

        return context

    def render_no_incomes(self):
        journal = utils.get_user().journal
        expenses = Expense.objects.last_months()
        pension = [*SavingBalance.objects.year(self._year, ["pensions"])]
        fund = [*SavingBalance.objects.year(self._year, ["shares", "funds"])]

        savings = None
        unnecessary = []

        if journal.unnecessary_expenses:
            arr = json.loads(journal.unnecessary_expenses)
            unnecessary = list(
                ExpenseType
                .objects
                .related()
                .filter(pk__in=arr)
                .values_list("title", flat=True)
            )

        if journal.unnecessary_savings:
            unnecessary.append(_('Savings'))
            savings = Saving.objects.last_months()

        avg_expenses, cut_sum = (
            no_incomes_data(
                expenses=expenses,
                savings=savings,
                not_use=unnecessary)
        )

        obj = NoIncomes(
            money=self._YearBalance.amount_end,
            fund=sum_col(fund, 'market_value'),
            pension=sum_col(pension, 'market_value'),
            avg_expenses=avg_expenses,
            cut_sum=cut_sum
        )

        context = {
            'no_incomes': obj.summary,
            'save_sum': cut_sum,
            'not_use': unnecessary,
            'avg_expenses': avg_expenses,
        }

        return render_to_string(
            'bookkeeping/includes/no_incomes.html',
            context,
            self._request
        )

    def render_wealth(self):
        money = (
            self._YearBalance.amount_end
            + sum_col(self._fund, 'market_value')
        )

        wealth = (
            self._YearBalance.amount_end
            + sum_col(self._fund, 'market_value')
        )
        wealth = wealth + sum_col(self._pension, 'market_value')

        context = {
            'title': [_('Money'), _('Wealth')],
            'data': [money, wealth],
        }
        return self._render_info_table(context)

    def render_averages(self):
        context = {
            'title': [_('Average incomes'), _('Average expenses')],
            'data': [self._YearBalance.avg_incomes, self._YearBalance.avg_expenses],
        }
        return self._render_info_table(context)

    def render_borrow(self):
        qs = Borrow.objects.sum_all()
        borrow = qs.get('borrow', 0)
        borrow_return = qs.get('borrow_return', 0)

        if borrow:
            context = {
                'title': [_('Borrow'), _('Borrow return')],
                'data': [borrow, borrow_return],
            }
            return self._render_info_table(context)
        else:
            return str()

    def render_lent(self):
        qs = Lent.objects.sum_all()
        lent = qs.get('lent', 0)
        lent_return = qs.get('lent_return', 0)

        if lent:
            context = {
                'title': [_('Lent'), _('Lent return')],
                'data': [lent, lent_return],
            }
            return self._render_info_table(context)
        else:
            return str()

    def _render_info_table(self, context):
        return render_to_string(
            'bookkeeping/includes/info_table.html',
            context,
            self._request
        )

    @staticmethod
    def percentage_from_incomes(incomes, savings):
        if incomes and savings:
            return (savings * 100) / incomes

        return 0

class ExpensesHelper():
    def __init__(self, request, year):
        self._request = request
        self._year = year

        qs_expenses = Expense.objects.sum_by_month_and_type(year)

        self._MonthExpense = MonthExpense(
            year=year,
            expenses=qs_expenses,
            expenses_types=expense_types())

    def render_chart_expenses(self):
        context = {
            'data': self._MonthExpense.chart_data
        }
        return render_to_string(
            'bookkeeping/includes/chart_expenses.html',
            context,
            self._request
        )

    def render_year_expenses(self):
        _expense_types = expense_types()

        context = {
            'year': self._year,
            'data': self._MonthExpense.balance,
            'categories': _expense_types,
            'total_row': self._MonthExpense.total_row,
            'avg_row': self._MonthExpense.average,
        }
        return render_to_string(
            'bookkeeping/includes/year_expenses.html',
            context,
            self._request
        )
