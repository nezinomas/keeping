from django.template.loader import render_to_string

from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin

from ..accounts.models import Account
from ..expenses.models import Expense, ExpenseType
from ..incomes.models import Income
from ..savings.models import Saving, SavingType
from ..transactions.models import SavingClose

from .lib import views_helpers
from .lib.account_stats import AccountStats
from .lib.helpers import create_month_list, current_day
from .lib.months_balance import MonthsBalance
from .lib.expense_type_stats import MonthExpenseType
from .lib.expense_type_stats import MonthsExpenseType
from .lib.no_incomes import NoIncomes
from .lib.saving_stats import SavingStats

from .forms import AccountWorthForm, SavingWorthForm
from .models import AccountWorth, SavingWorth


def _account_stats(request):
    _stats = Account.objects.balance_year(request.user.profile.year)
    _worth = AccountWorth.objects.items()

    return AccountStats(_stats, _worth)


def _saving_stats(year):
    _stats = SavingType.objects.balance_year(year)
    _worth = SavingWorth.objects.items()

    fund = SavingStats(_stats, _worth, 'fund')
    pension = SavingStats(_stats, _worth, 'pension')

    return fund, pension


def _render_account_stats(request, account, **kwargs):
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


def _render_saving_stats(request, fund, pension, **kwargs):
    return render_to_string(
        'bookkeeping/includes/savings_worth_list.html',
        {
            'fund': fund.balance, 'fund_totals': fund.totals,
            'pension': pension.balance, 'pension_totals': pension.totals,
            **kwargs
        },
        request
    )


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        _account = _account_stats(self.request)
        _fund, _pension = _saving_stats(year)

        qs_income = Income.objects.income_sum(year)
        qs_expense = Expense.objects.month_expense(year)
        qs_savings = Saving.objects.month_saving(year)
        qs_savings_close = SavingClose.objects.month_sum(year)
        qs_expense_types = views_helpers.expense_types('Taupymas')

        _MonthsBalance = MonthsBalance(
            year=year, incomes=qs_income, expenses=qs_expense,
            savings=qs_savings, savings_close=qs_savings_close,
            amount_start=_account.balance_start)

        qs_ExpenseType = Expense.objects.month_expense_type(year)
        _MonthExpenseType = MonthsExpenseType(year, qs_ExpenseType)

        _NoIncomes = NoIncomes(
            money=_MonthsBalance.amount_end,
            fund=_fund.total_market,
            pension=_pension.total_market,
            avg_expenses=_MonthsBalance.avg_expenses,
            avg_type_expenses=_MonthExpenseType.average,
            not_use=['Darbas', 'Laisvalaikis', 'Paskolos', 'Taupymas', 'Transportas']
        )

        context['accounts'] = _render_account_stats(
            self.request, _account, **{'months_amount_end': _MonthsBalance.amount_end})
        context['savings'] = _render_saving_stats(self.request, _fund, _pension)
        context['balance'] = _MonthsBalance.balance
        context['balance_totals'] = _MonthsBalance.totals
        context['balance_avg'] = _MonthsBalance.average
        context['amount_start'] = _MonthsBalance.amount_start
        context['months_amount_end'] = _MonthsBalance.amount_end
        context['accounts_amount_end'] = _account.balance_end
        context['amount_balance'] = _MonthsBalance.amount_balance
        context['total_market'] = _fund.total_market
        context['avg_incomes'] = _MonthsBalance.avg_incomes
        context['avg_expenses'] = _MonthsBalance.avg_expenses
        context['expenses'] = _MonthExpenseType.balance
        context['expense_types'] = qs_expense_types
        context['expenses_totals'] = _MonthExpenseType.totals
        context['expenses_average'] = _MonthExpenseType.average
        context['no_incomes'] = _NoIncomes.summary
        context['save_sum'] = _NoIncomes.save_sum

        # charts data
        context['pie'] = _MonthExpenseType.chart_data
        context['e'] = _MonthsBalance.expense_data
        context['i'] = _MonthsBalance.income_data
        context['s'] = _MonthsBalance.save_data

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _fund, _pension = _saving_stats(self.request.user.profile.year)

        context['fund'] = _fund.balance
        context['fund_totals'] = _fund.totals
        context['pension'] = _pension.balance
        context['pension_totals'] = _pension.totals

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _account = _account_stats(self.request)

        context['accounts'] = _account.balance
        context['totals'] = _account.totals

        return context


class Month(IndexMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year
        month = self.request.user.profile.month

        _MonthExpenseType = MonthExpenseType(
            year,
            month,
            Expense.objects.day_expense_type(year, month)
        )
        context['month_list'] = create_month_list(year)
        context['expenses'] = _MonthExpenseType.balance
        context['expense_types'] = views_helpers.expense_types('Taupymas')
        context['day'] = current_day(year, month)

        return context
