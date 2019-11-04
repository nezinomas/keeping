from typing import Dict, List

from django.template.loader import render_to_string

from ...core.lib.utils import sum_all, sum_col
from ...expenses.models import ExpenseType


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
