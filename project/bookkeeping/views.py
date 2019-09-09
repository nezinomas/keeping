from django.template.loader import render_to_string

from ..accounts.models import Account
from ..core.mixins.views import CreateAjaxMixin, IndexMixin
from ..core.mixins.formset import FormsetMixin
from ..expenses.models import Expense
from ..incomes.models import Income
from ..savings.models import Saving, SavingType
from ..transactions.models import SavingChange, SavingClose, Transaction

from . import forms, models

from .lib.get_data import GetObjects
from .lib.stats_accounts import StatsAccounts
from .lib.stats_savings import StatsSavings

from .lib.account_stats import AccountStats

def _get_stats(request):
    objects = GetObjects([
        Account, Income, Expense, Transaction,
        SavingType, Saving, SavingChange, SavingClose,
        models.SavingWorth, models.AccountWorth
    ])

    accounts = StatsAccounts(request.user.profile.year, objects.data)
    savings = StatsSavings(request.user.profile.year, objects.data)

    return accounts, savings


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Account and AccountWorth stats
        _account_stats = Account.objects.balance_year(self.request.user.profile.year)
        _account_worth = models.AccountWorth.objects.items()
        _account = AccountStats(_account_stats, _account_worth)

        context['accounts'] = render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {
                'accounts': _account.balance,
                'totals': _account.totals
            },
            self.request
        )

        # Saving and SawingWorth stats
        accounts, savings = _get_stats(self.request)

        context['savings'] = render_to_string(
            'bookkeeping/includes/savings_worth_list.html',
            {'savings': savings.balance},
            self.request
        )

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = models.SavingWorth
    form_class = forms.SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _, savings = _get_stats(self.request)
        context['savings'] = savings.balance

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = models.AccountWorth
    form_class = forms.AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _account_stats = Account.objects.balance_year(self.request.user.profile.year)
        _account_worth = models.AccountWorth.objects.items()
        _account = AccountStats(_account_stats, _account_worth)

        context['accounts'] = _account.balance
        context['totals'] = _account.totals

        return context
