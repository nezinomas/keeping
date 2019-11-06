from typing import Dict, List

from django.template.loader import render_to_string

from ...core.lib.utils import sum_all, sum_col
from ...expenses.models import ExpenseType
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
