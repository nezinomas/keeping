from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..accounts.models import Account
from ..expenses.models import Expense
from ..incomes.models import Income
from ..savings.models import Saving, SavingType
from ..transactions.models import Transaction, SavingChange, SavingClose
from .lib.get_data import GetObjects
from .lib.stats_accounts import StatsAccounts
from .lib.stats_savings import StatsSavings


@login_required()
def index(request):
    objects = GetObjects([
        Account, Income, Expense, Transaction,
        SavingType, Saving, SavingChange, SavingClose
    ])

    accounts = StatsAccounts(request.user.profile.year, objects.data)
    savings = StatsSavings(request.user.profile.year, objects.data)

    context = {
        'accounts': accounts.balance,
        'savings': savings.balance,
        'past_amount': accounts.past_amount,
        'current_amount': accounts.current_amount,
    }

    return render(request, 'bookkeeping/main.html', context=context)
