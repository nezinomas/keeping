from django.template.loader import render_to_string

from ..accounts.models import Account
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin
from ..savings.models import SavingType
from . import forms
from .lib.account_stats import AccountStats
from .lib.saving_stats import SavingStats
from .models import AccountWorth, SavingWorth


def _account_stats(request):
    _stats = Account.objects.balance_year(request.user.profile.year)
    _worth = AccountWorth.objects.items()

    return AccountStats(_stats, _worth)


def _saving_stats(request):
    _stats = SavingType.objects.balance_year(request.user.profile.year)
    _worth = SavingWorth.objects.items()

    return SavingStats(_stats, _worth)


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Account and AccountWorth stats
        account = _account_stats(self.request)

        context['accounts'] = render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {
                'accounts': account.balance,
                'totals': account.totals
            },
            self.request
        )

        # Saving and SawingWorth stats
        saving = _saving_stats(self.request)

        context['savings'] = render_to_string(
            'bookkeeping/includes/savings_worth_list.html',
            {
                'savings': saving.balance,
                'totals': saving.totals
            },
            self.request
        )

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = forms.SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        saving = _saving_stats(self.request)

        context['savings'] = saving.balance
        context['totals'] = saving.totals

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = forms.AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = _account_stats(self.request)

        context['accounts'] = account.balance
        context['totals'] = account.totals

        return context
