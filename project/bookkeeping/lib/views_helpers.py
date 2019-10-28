from typing import List

from django.template.loader import render_to_string

from ...core.lib.utils import sum_all, sum_col
from ...expenses.models import ExpenseType
from ...savings.models import SavingBalance


def expense_types(*args: str) -> List[str]:
    qs = list(ExpenseType.objects.all().values_list('title', flat=True))

    [qs.append(x) for x in args]

    qs.sort()

    return qs


def necessary_expense_types(*args: str) -> List[str]:
    qs = list(ExpenseType.objects.filter(necessary=True).values_list('title', flat=True))

    [qs.append(x) for x in args]

    qs.sort()

    return qs


def split_savings_stats(year):
    arr = SavingBalance.objects.items(year)

    fund = list(filter(lambda x: 'pens' not in x['title'].lower(), arr))
    pension = list(filter(lambda x: 'pens' in x['title'].lower(), arr))

    return fund, pension


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


def render_savings(request, fund, pension, **kwargs):
    return render_to_string(
        'bookkeeping/includes/savings_worth_list.html',
        {
            'fund': fund, 'fund_total_row': sum_all(pension),
            'pension': pension, 'pension_total_row': sum_all(pension),
            **kwargs
        },
        request
    )
