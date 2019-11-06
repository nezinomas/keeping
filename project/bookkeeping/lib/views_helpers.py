from typing import Dict, List

from django.template.loader import render_to_string

from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict as get_val
from ...core.lib.utils import sum_all, sum_col
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import CalcDaySum
from ...savings.models import Saving
from ..lib.day_spending import DaySpending
from ..lib.expense_summary import DayExpense


def expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType.objects.items()
        .values_list('title', flat=True)
    )

    [qs.append(x) for x in args]

    qs.sort()

    return qs


def necessary_expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType.objects.items()
        .filter(necessary=True)
        .values_list('title', flat=True)
    )

    [qs.append(x) for x in args]

    qs.sort()

    return qs


def split_funds(lst: List[Dict], key: str) -> List[Dict]:
    return list(filter(lambda x: key in x['title'].lower(), lst))


def render_accounts(request, account, **kwargs):
    return render_to_string(
        'bookkeeping/includes/accounts_worth_list.html',
        {
            'accounts': account,
            'total_row': sum_all(account),
            'accounts_amount_end': sum_col(account, 'balance'),
            **kwargs
        },
        request
    )


def render_savings(request, fund, **kwargs):
    return render_to_string(
        'bookkeeping/includes/savings_worth_list.html',
        {
            'fund': fund, 'fund_total_row': sum_all(fund),
            **kwargs
        },
        request
    )


def render_pensions(request, pension, **kwargs):
    return render_to_string(
        'bookkeeping/includes/pensions_worth_list.html',
        {
            'pension': pension, 'pension_total_row': sum_all(pension),
            **kwargs
        },
        request
    )


class MonthHelper():
    def __init__(self, request, year, month):
        self.request = request
        self.year = year
        self.month = month

        qs_expenses = Expense.objects.day_expense_type(year, month)
        qs_savings = Saving.objects.day_saving(year, month)

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

        self.expenses_types = expense_types('Taupymas')
        self.current_day = current_day(year, month)

    def render_chart_targets(self):
        targets = self._day_plans.targets(self.month, 'Taupymas')
        (categories, data_target, data_fact) = self._day.chart_targets(
            self.expenses_types, targets)

        context = {
            'chart_targets_categories': categories,
            'chart_targets_data_target': data_target,
            'chart_targets_data_fact': data_fact,
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_targets.html',
            context=context,
            request=self.request
        )

    def render_chart_expenses(self):
        context = {
            'expenses': self._day.chart_expenses(self.expenses_types)
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_expenses.html',
            context=context,
            request=self.request
        )

    def render_spending(self):
        context = {
            'spending_table': self._spending.spending,
            'day': self.current_day,
        }

        return render_to_string(
            template_name='bookkeeping/includes/spending.html',
            context=context,
            request=self.request
        )

    def render_info(self):
        fact_incomes = Income.objects.income_sum(self.year, self.month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_expenses = self._day.total

        plan_incomes = get_val(self._day_plans.incomes, self.month)
        plan_day_sum = get_val(self._day_plans.day_input, self.month)
        plan_free_sum = get_val(self._day_plans.expenses_free, self.month)
        plan_remains = get_val(self._day_plans.remains, self.month)

        context = {
            'plan_per_day': plan_day_sum,
            'plan_incomes': plan_incomes,
            'plan_remains': plan_remains,
            'fact_per_day': self._spending.avg_per_day,
            'fact_incomes': fact_incomes,
            'fact_remains': fact_incomes - fact_expenses,
        }

        return render_to_string(
            template_name='bookkeeping/includes/spending_info.html',
            context=context,
            request=self.request
        )

    def render_month_table(self):
        context = {
            'expenses': self._day.balance,
            'total_row': self._day.total_row,
            'expense_types': self.expenses_types,
            'day': self.current_day,
        }

        return render_to_string(
            template_name='bookkeeping/includes/month_table.html',
            context=context,
            request=self.request
        )
