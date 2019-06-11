from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..accounts.models import Account
from ..expenses.models import Expense
from ..incomes.models import Income
from ..savings.models import Saving, SavingType
from ..transactions.models import Transaction
from .lib.get_data import GetObjects
from .lib.stats_accounts import StatsAccounts


@login_required()
def index(request):
    objects = GetObjects([Account, Income, Expense, Saving, Transaction])
    stats = StatsAccounts(request.user.profile.year, objects.data)
    context = {'tbl': stats.balance}

    return render(request, 'bookkeeping/main.html', context=context)
