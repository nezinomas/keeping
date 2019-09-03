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

        accounts, savings = _get_stats(self.request)

        context['accounts'] = render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {'accounts': accounts.balance},
            self.request
        )
        context['savings'] = render_to_string(
            'bookkeeping/includes/savings_worth_list.html',
            {'savings': savings.balance},
            self.request
        )
        context['past_amount'] = accounts.past_amount
        context['current_amount'] = accounts.current_amount

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

        accounts, _ = _get_stats(self.request)
        context['accounts'] = accounts.balance

        return context
