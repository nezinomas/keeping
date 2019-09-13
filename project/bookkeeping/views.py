from django.template.loader import render_to_string

from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin

from ..accounts.models import Account
from ..expenses.models import Expense
from ..incomes.models import Income
from ..savings.models import SavingType

from .lib.account_stats import AccountStats
from .lib.months_balance import MonthsBalance
from .lib.saving_stats import SavingStats

from .forms import AccountWorthForm, SavingWorthForm
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

        year = self.request.user.profile.year

        incomes = Income.objects.income_sum(year, 'incomes')
        expenses = Expense.objects.expense_sum(year, 'expenses')
        o = MonthsBalance(incomes, expenses, account.balance_start)

        context['balance'] = o.balance
        context['balance_totals'] = o.totals
        context['balance_avg'] = o.average
        context['amount_start'] = o.amount_start
        context['amount_end'] = o.amount_end

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        saving = _saving_stats(self.request)

        context['savings'] = saving.balance
        context['totals'] = saving.totals

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = _account_stats(self.request)

        context['accounts'] = account.balance
        context['totals'] = account.totals

        return context
