from typing import Dict, List

from django.template.loader import render_to_string

from ...core.lib.utils import get_value_from_dict, sum_all, sum_col
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


def render_chart_targets(request,
                         day_expense: DayExpense,
                         targets: Dict,
                         expenses_types: List):
    context = {}

    (categories, data_target, data_fact) = day_expense.chart_targets(
        expenses_types, targets)

    context['chart_targets_categories'] = categories
    context['chart_targets_data_target'] = data_target
    context['chart_targets_data_fact'] = data_fact

    return render_to_string(
        template_name='bookkeeping/includes/chart_target.html',
        context=context,
        request=request
    )


def render_chart_expenses(request,
                          day_expense: DayExpense,
                          expenses_types: List):
    context = {}
    context['expenses'] = day_expense.chart_expenses(expenses_types)

    return render_to_string(
        template_name='bookkeeping/includes/chart_month_expenses.html',
        context=context,
        request=request
    )


def render_spending(request,
                    current_day: int,
                    spending: List[Dict]):
    context = {}
    context['spending_table'] = spending
    context['day'] = current_day

    return render_to_string(
        template_name='bookkeeping/includes/month_day_spending.html',
        context=context,
        request=request
    )


class MonthHelper():
    def __init__(self, year, month):
        self.year = year
        self.month = month

        self._DayExpense = DayExpense(
            year,
            month,
            Expense.objects.day_expense_type(self.year, self.month),
            **{'Taupymas': Saving.objects.day_saving(self.year, self.month)}
        )

        self._CalcDaySum = CalcDaySum(self.year)

        self._DaySpending = DaySpending(
            year=self.year,
            month=self.month,
            month_df=self._DayExpense.expenses,
            necessary=necessary_expense_types('Taupymas'),
            plan_day_sum=get_value_from_dict(
                self._CalcDaySum.day_input, month),
            plan_free_sum=get_value_from_dict(
                self._CalcDaySum.expenses_free, month),
            exceptions=self._DayExpense.exceptions
        )

        self.expenses_types = expense_types('Taupymas')
        targets = self._CalcDaySum.targets(month, 'Taupymas')

    def render_info(self, request):
        fact_incomes = Income.objects.income_sum(self.year, self.month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_expenses = self._DayExpense.total

        plan_incomes = get_value_from_dict(
            self._CalcDaySum.incomes, self.month)
        plan_day_sum = get_value_from_dict(
            self._CalcDaySum.day_input, self.month)
        plan_free_sum = get_value_from_dict(
            self._CalcDaySum.expenses_free, self.month)
        plan_remains = get_value_from_dict(
            self._CalcDaySum.remains, self.month)

        info = {
            'plan_per_day': plan_day_sum,
            'plan_incomes': plan_incomes,
            'plan_remains': plan_remains,
            'fact_per_day': self._DaySpending.avg_per_day,
            'fact_incomes': fact_incomes,
            'fact_remains': fact_incomes - fact_expenses,
        }

        return render_to_string(
            template_name='bookkeeping/includes/month_spending_info.html',
            context=info,
            request=request
        )
