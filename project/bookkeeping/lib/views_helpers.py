import itertools as it
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List

from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string

from ...accounts.models import AccountBalance
from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict as get_val
from ...core.lib.utils import sum_all, sum_col
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


def split_funds(lst: List[Dict], key: str) -> List[Dict]:
    trues = []
    falses = []

    for x in lst:
        if key in x['title'].lower():
            trues.append(x)
        else:
            falses.append(x)

    return trues, falses


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


def percentage_from_incomes(incomes, savings):
    if incomes and savings:
        return (savings * 100) / incomes

    return 0


def average(qs):
    now = datetime.now()
    arr = []

    for r in qs:
        year = r['year']
        sum_val = float(r['sum'])

        cnt = now.month if year == now.year else 12

        arr.append(sum_val / cnt)

    return arr


# ---------------------------------------------------------------------------------------
#                                                                             No Incomes
# --------------------------------------------------------------------------------------
NOT_USE = [
    'Darbas',
    'Laisvalaikis',
    'Taupymas',
    'Buitinės',
]


def no_incomes_data(expenses, savings=None, not_use=None):
    months = 6
    not_use = not_use if not_use else []

    # if today February, then end is 2020-01-31
    end = date.today().replace(day=1) - timedelta(days=1)

    # back months to past; if months=6 then start=2019-08-01
    start = (end + timedelta(days=1)) - relativedelta(months=months)

    expenses_sum = 0.0
    cut_sum = 0.0
    for r in expenses:
        if r['date'] >= start and r['date'] <= end:
            expenses_sum += float(r['sum'])

            if r['title'] in not_use:
                cut_sum += float(r['sum'])


    savings_sum = 0.0
    if savings:
        for r in savings:
            if r['date'] >= start and r['date'] <= end:
                savings_sum += float(r['sum'])

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
            **{'Taupymas': qs_savings}
        )

        self._day_plans = CalcDaySum(year)

        self._spending = DaySpending(
            year=year,
            month=month,
            month_df=self._day.expenses,
            exceptions=self._day.exceptions,
            necessary=necessary_expense_types('Taupymas'),
            plan_day_sum=get_val(self._day_plans.day_input, month),
            plan_free_sum=get_val(self._day_plans.expenses_free, month),
        )

        self._expenses_types = expense_types('Taupymas')

    def render_chart_targets(self):
        targets = self._day_plans.targets(self._month, 'Taupymas')
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
        self.qs_savings = Saving.objects.sum_by_month(year)
        qs_savings_close = SavingClose.objects.sum_by_month(year)
        self.qs_ExpenseType = Expense.objects.sum_by_month_and_type(year)

        self._MonthExpense = MonthExpense(
            year, self.qs_ExpenseType, **{'Taupymas': self.qs_savings})

        self._YearBalance = YearBalance(
            year=year,
            incomes=qs_income,
            expenses=self._MonthExpense.total_column,
            savings_close=qs_savings_close,
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
        context = {
            'amount_start': self._YearBalance.amount_start,
            'months_amount_end': self._YearBalance.amount_end,
            'amount_balance': self._YearBalance.amount_balance,
        }
        return render_to_string(
            'bookkeeping/includes/year_balance_short.html',
            context,
            self._request
        )

    def render_chart_expenses(self):
        context = {
            'data': self._MonthExpense.chart_data
        }
        return render_to_string(
            'bookkeeping/includes/chart_expenses.html',
            context,
            self._request
        )

    def render_chart_balance(self):
        context = {
            'e': self._YearBalance.expense_data,
            'i': self._YearBalance.income_data,
            's': self._YearBalance.save_data,
        }

        return render_to_string(
            'bookkeeping/includes/chart_balance.html',
            context,
            self._request
        )

    def render_year_expenses(self):
        _expense_types = expense_types('Taupymas')

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

    def render_accounts(self):
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
        total_row = sum_all(self._fund)

        context = {
            'title': 'Fondai',
            'items': self._fund,
            'total_row': total_row,
            'percentage_from_incomes': (
                percentage_from_incomes(
                    incomes=self._YearBalance.total_row.get('incomes'),
                    savings=self._MonthExpense.total_row.get('Taupymas'))
            ),
            'profit_incomes_proc': (
                percentage_from_incomes(
                    total_row.get('incomes'),
                    total_row.get('market_value')
                ) - 100
            ),
            'profit_invested_proc': (
                percentage_from_incomes(
                    total_row.get('invested'),
                    total_row.get('market_value')
                ) - 100
            ),
        }

        return render_to_string(
            'bookkeeping/includes/worth_table.html',
            context,
            self._request
        )

    def render_pensions(self):
        context = {
            'title': 'Pensija',
            'items': self._pension,
            'total_row': sum_all(self._pension),
        }

        return render_to_string(
            'bookkeeping/includes/worth_table.html',
            context,
            self._request
        )

    def render_no_incomes(self):
        pension, fund = split_funds(self._fund, 'invl')
        avg_expenses, cut_sum = (
            no_incomes_data(
                expenses=self.qs_ExpenseType,
                savings=self.qs_savings,
                not_use=NOT_USE)
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
            'not_use': NOT_USE,
            'avg_expenses': avg_expenses,
        }

        return render_to_string(
            'bookkeeping/includes/no_incomes.html',
            context,
            self._request
        )

    def render_money(self):
        wealth_money = (
            self._YearBalance.amount_end
            + sum_col(self._fund, 'market_value')
        )
        context = {
            'title': 'Pinigai',
            'data': wealth_money,
        }
        return self._render_info_table(context)

    def render_wealth(self):
        wealth_money = (
            self._YearBalance.amount_end
            + sum_col(self._fund, 'market_value')
        )
        wealth = wealth_money + sum_col(self._pension, 'market_value')

        context = {
            'title': 'Turtas',
            'data': wealth,
        }
        return self._render_info_table(context)

    def render_avg_incomes(self):
        context = {
            'title': 'Vidutinės pajamos',
            'data': self._YearBalance.avg_incomes,
        }
        return self._render_info_table(context)

    def render_avg_expenses(self):
        context = {
            'title': 'Vidutinės išlaidos',
            'data': self._YearBalance.avg_expenses,
        }
        return self._render_info_table(context)

    def _render_info_table(self, context):
        return render_to_string(
            'bookkeeping/includes/info_table.html',
            context,
            self._request
        )
