from django.template.loader import render_to_string

from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin

from ..accounts.models import Account
from ..expenses.models import Expense, ExpenseType
from ..incomes.models import Income
from ..savings.models import SavingType

from .lib.account_stats import AccountStats
from .lib.months_balance import MonthsBalance
from .lib.saving_stats import SavingStats
from .lib.months_expense_type import MonthsExpenseType

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

        year = self.request.user.profile.year

        # Account and AccountWorth stats
        account = _account_stats(self.request)

        context['accounts'] = render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {'accounts': account.balance, 'totals': account.totals},
            self.request
        )

        # Saving and SawingWorth stats
        saving = _saving_stats(self.request)

        context['savings'] = render_to_string(
            'bookkeeping/includes/savings_worth_list.html',
            {'savings': saving.balance, 'totals': saving.totals},
            self.request
        )

        incomes = Income.objects.income_sum(year)
        expenses = Expense.objects.expense_sum(year)
        o = MonthsBalance(year, incomes, expenses, account.balance_start)

        context['balance'] = o.balance
        context['balance_totals'] = o.totals
        context['balance_avg'] = o.average
        context['amount_start'] = o.amount_start
        context['amount_end'] = o.amount_end

        expenses = Expense.objects.expense_type_sum(year)
        oe = MonthsExpenseType(expenses)

        context['expenses'] = oe.balance
        context['expense_types'] = (
            ExpenseType.objects.all()
            .values_list('title', flat=True)
        )
        context['expenses_totals'] = oe.totals
        context['expenses_average'] = oe.average

        arr = oe.totals
        del arr['total']
        l = [{'name': k, 'y': v} for k, v in arr.items()]

        # charts data
        context['pie'] = l
        context['e'] = o.expense_data
        context['i'] = o.income_data
        context['s'] = o.save_data

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
