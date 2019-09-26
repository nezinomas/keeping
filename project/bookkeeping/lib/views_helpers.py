from django.template.loader import render_to_string

from ...accounts.models import Account
from ...expenses.models import ExpenseType
from ...savings.models import SavingType

from ..lib.account_stats import AccountStats
from ..lib.saving_stats import SavingStats

from ..models import AccountWorth, SavingWorth


def expense_types(*args):
    qs = list(ExpenseType.objects.all().values_list('title', flat=True))

    [qs.append(x) for x in args]

    qs.sort()

    return list(qs)


def account_stats(year):
    _stats = Account.objects.balance_year(year)
    _worth = AccountWorth.objects.items()

    return AccountStats(_stats, _worth)


def saving_stats(year):
    _stats = SavingType.objects.balance_year(year)
    _worth = SavingWorth.objects.items()

    fund = SavingStats(_stats, _worth, 'fund')
    pension = SavingStats(_stats, _worth, 'pension')

    return fund, pension


def render_account_stats(request, account, **kwargs):
        return render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {
                'accounts': account.balance,
                'totals': account.totals,
                'accounts_amount_end': account.balance_end,
                **kwargs
            },
            request
        )


def render_saving_stats(request, fund, pension, **kwargs):
    return render_to_string(
        'bookkeeping/includes/savings_worth_list.html',
        {
            'fund': fund.balance, 'fund_totals': fund.totals,
            'pension': pension.balance, 'pension_totals': pension.totals,
            **kwargs
        },
        request
    )
