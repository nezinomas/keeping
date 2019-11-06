from django.shortcuts import render
from django.template.loader import render_to_string

from ..accounts.models import Account, AccountBalance
from ..core.lib.summary import collect_summary_data
from ..core.lib.utils import sum_all, sum_col
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import PensionBalance, PensionType
from ..plans.models import DayPlan
from ..savings.models import Saving, SavingBalance, SavingType
from ..transactions.models import SavingClose
from .forms import AccountWorthForm, PensionWorthForm, SavingWorthForm
from .lib import views_helpers as H
from .lib.expense_summary import MonthExpense
from .lib.no_incomes import NoIncomes
from .lib.year_balance import YearBalance
from .models import AccountWorth, PensionWorth, SavingWorth


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        _account = [*AccountBalance.objects.items(year)]
        _fund = [*SavingBalance.objects.items(year)]
        _pension = [*PensionBalance.objects.items(year)]
        _expense_types = H.expense_types('Taupymas')

        qs_income = Income.objects.income_sum(year)
        qs_savings = Saving.objects.month_saving(year)
        qs_savings_close = SavingClose.objects.month_sum(year)
        qs_ExpenseType = Expense.objects.month_expense_type(year)

        _MonthExpense = MonthExpense(
            year, qs_ExpenseType, **{'Taupymas': qs_savings})

        _YearBalance = YearBalance(
            year=year,
            incomes=qs_income,
            expenses=_MonthExpense.total_column,
            savings_close=qs_savings_close,
            amount_start=sum_col(_account, 'past'))

        wealth_money = _YearBalance.amount_end + sum_col(_fund, 'market_value')
        wealth = wealth_money + sum_col(_pension, 'market_value')

        _NoIncomes = NoIncomes(
            money=wealth_money,
            fund=sum_col(H.split_funds(_fund, 'lx'), 'market_value'),
            pension=sum_col(H.split_funds(_fund, 'invl'), 'market_value'),
            avg_expenses=_YearBalance.avg_expenses,
            avg_type_expenses=_MonthExpense.average,
            not_use=[
                'Darbas',
                'Laisvalaikis',
                'Paskolos',
                'Taupymas',
                'Transportas']
        )

        context['year'] = year
        context['accounts'] = H.render_accounts(
            self.request, _account,
            **{'months_amount_end': _YearBalance.amount_end})
        context['savings'] = H.render_savings(self.request, _fund)
        context['pensions'] = H.render_pensions(self.request, _pension)
        context['balance'] = _YearBalance.balance
        context['balance_total_row'] = _YearBalance.total_row
        context['balance_avg'] = _YearBalance.average
        context['amount_start'] = _YearBalance.amount_start
        context['months_amount_end'] = _YearBalance.amount_end
        context['accounts_amount_end'] = sum_col(_account, 'balance')
        context['amount_balance'] = _YearBalance.amount_balance
        context['avg_incomes'] = _YearBalance.avg_incomes
        context['avg_expenses'] = _YearBalance.avg_expenses
        context['expenses'] = _MonthExpense.balance
        context['expense_types'] = _expense_types
        context['expenses_total_row'] = _MonthExpense.total_row
        context['expenses_average'] = _MonthExpense.average
        context['no_incomes'] = _NoIncomes.summary
        context['save_sum'] = _NoIncomes.save_sum
        context['wealth_money'] = wealth_money
        context['wealth'] = wealth

        # charts data
        context['pie'] = _MonthExpense.chart_data
        context['e'] = _YearBalance.expense_data
        context['i'] = _YearBalance.income_data
        context['s'] = _YearBalance.save_data

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.profile.year

        _fund = SavingBalance.objects.items(year)

        context['fund'] = _fund
        context['fund_total_row'] = sum_all(_fund)

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.profile.year

        qsa = Account.objects.items().values('id', 'title')
        typesa = {x['title']: x['id'] for x in qsa}
        acc = collect_summary_data(year, typesa, 'accounts')

        _account = AccountBalance.objects.items()

        context['accounts'] = _account
        context['total_row'] = sum_all(_account)

        return context


class PensionsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = PensionType
    model = PensionWorth
    form_class = PensionWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.profile.year

        _pension = PensionBalance.objects.items(year)

        context['pension'] = _pension
        context['pension_total_row'] = sum_all(_pension)

        return context


class Month(IndexMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return _month_context(self.request, context)


def reload_month(request):
    template = 'bookkeeping/includes/reload_month.html'
    ajax_trigger = request.GET.get('ajax_trigger')

    year = request.user.profile.year
    month = request.user.profile.month

    context = {}

    if ajax_trigger:
        context = _month_context(request, context)

        return render(request, template, context)


def _month_context(request, context):
    year = request.user.profile.year
    month = request.user.profile.month

    obj = H.MonthHelper(request, year, month)

    context['month_table'] = obj.render_month_table()
    context['spending'] = obj.render_spending()
    context['info'] = obj.render_info()
    context['chart_expenses'] = obj.render_chart_expenses()
    context['chart_targets'] = obj.render_chart_targets()

    return context
