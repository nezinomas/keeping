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
from .lib.no_incomes import NoIncomes
from .lib.months_expense_type import MonthsExpenseType

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


def _render_account_stats(request, account):
        return render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            {'accounts': account.balance, 'totals': account.totals},
            request
        )


def _render_saving_stats(request, fund, pension):
    return render_to_string(
        'bookkeeping/includes/savings_worth_list.html',
        {
            'fund': fund.balance, 'fund_totals': fund.totals,
            'pension': pension.balance, 'pension_totals': pension.totals,
        },
        request
    )


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        obj_account = _account_stats(self.request)
        obj_fund, obj_pension = _saving_stats(year)

        qs_income = Income.objects.income_sum(year)
        qs_expense = Expense.objects.expense_sum(year)
        obj_MonthsBalance = MonthsBalance(
            year, qs_income, qs_expense, obj_account.balance_start)

        qs_ExpenseType = Expense.objects.expense_type_sum(year)
        obj_MonthExpenseType = MonthsExpenseType(year, qs_ExpenseType)

        no_incomes = NoIncomes(
            money=obj_MonthsBalance.amount_end,
            fund=obj_fund.total_market,
            pension=obj_pension.total_market,
            avg_expenses=obj_MonthsBalance.avg_expenses,
            avg_type_expenses=obj_MonthExpenseType.average,
            not_use=['Darbas', 'Laisvalaikis', 'Paskolos', 'Taupymas', 'Transportas']
        )

        context['accounts'] = _render_account_stats(self.request, obj_account)
        context['savings'] = _render_saving_stats(self.request, obj_fund, obj_pension)
        context['balance'] = obj_MonthsBalance.balance
        context['balance_totals'] = obj_MonthsBalance.totals
        context['balance_avg'] = obj_MonthsBalance.average
        context['amount_start'] = obj_MonthsBalance.amount_start
        context['amount_end'] = obj_MonthsBalance.amount_end
        context['amount_balance'] = obj_MonthsBalance.amount_balance
        context['total_market'] = obj_fund.total_market
        context['avg_incomes'] = obj_MonthsBalance.avg_incomes
        context['avg_expenses'] = obj_MonthsBalance.avg_expenses
        context['expenses'] = obj_MonthExpenseType.balance
        context['expense_types'] = (
            ExpenseType.objects.all()
            .values_list('title', flat=True)
        )
        context['expenses_totals'] = obj_MonthExpenseType.totals
        context['expenses_average'] = obj_MonthExpenseType.average
        context['no_incomes'] = no_incomes.summary
        context['save_sum'] = no_incomes.save_sum

        # charts data
        context['pie'] = obj_MonthExpenseType.chart_data
        context['e'] = obj_MonthsBalance.expense_data
        context['i'] = obj_MonthsBalance.income_data
        context['s'] = obj_MonthsBalance.save_data

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj_fund, obj_pension = _saving_stats(self.request.user.profile.year)

        context['fund'] = obj_fund.balance
        context['fund_totals'] = obj_fund.totals
        context['pension'] = obj_pension.balance
        context['pension_totals'] = obj_pension.totals

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj_account = _account_stats(self.request)

        context['accounts'] = obj_account.balance
        context['totals'] = obj_account.totals

        return context
