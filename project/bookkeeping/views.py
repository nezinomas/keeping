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
from .lib.saving_stats import SavingStats


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Account and AccountWorth stats
        _account_stats = Account.objects.balance_year(self.request.user.profile.year)
        _account_worth = models.AccountWorth.objects.items()
        _account = AccountStats(list(_account_stats), list(_account_worth))

        context['accounts'] = render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {
                'accounts': _account.balance,
                'totals': _account.totals
            },
            self.request
        )

        # Saving and SawingWorth stats
        _saving_stats = SavingType.objects.balance_year(self.request.user.profile.year)
        _saving_worth = models.SavingWorth.objects.items()
        _saving = SavingStats(_saving_stats, _saving_worth)

        context['savings'] = render_to_string(
            'bookkeeping/includes/savings_worth_list.html',
            {
                'savings': _saving.balance,
                'totals': _saving.totals
            },
            self.request
        )

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = models.SavingWorth
    form_class = forms.SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _saving_stats = SavingType.objects.balance_year(
            self.request.user.profile.year)
        _saving_worth = models.SavingWorth.objects.items()
        _saving = SavingStats(_saving_stats, _saving_worth)

        context['savings'] = _savings.balance
        context['totals'] = _savings.totals

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
