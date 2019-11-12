from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from ..accounts.models import Account, AccountBalance
from ..core.lib.date import year_month_list
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

        obj = H.IndexHelper(self.request, year)

        context['year'] = year
        context['accounts'] = obj.render_accounts()
        context['savings'] = obj.render_savings()
        context['pensions'] = obj.render_pensions()
        context['year_balance'] = obj.render_year_balance()
        context['year_balance_short'] = obj.render_year_balance_short()
        context['year_expenses'] = obj.render_year_expenses()

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
        context['no_incomes'] = obj.render_no_incomes()

        context['money'] = obj.render_money()
        context['wealth'] = obj.render_wealth()

        # charts data
        context['chart_expenses'] = obj.render_chart_expenses()
        context['chart_balance'] = obj.render_chart_balance()

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

        _account = AccountBalance.objects.items(year)

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

        context['buttons'] = year_month_list()
        context = _month_context(self.request, context)

        return context


class Detailed(LoginRequiredMixin, TemplateView):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        context['months'] = range(1, 13)
        context['data'] = []

        # Incomes
        qs = Income.objects.month_type_sum(year)
        total_row = H.sum_detailed(qs, 'date', ['sum'])
        total_col = H.sum_detailed(qs, 'title', ['sum'])
        total = sum_col(total_col, 'sum')

        context['data'].append({
            'name': 'Pajamos',
            'data': qs,
            'total_row': total_row,
            'total_col': total_col,
            'total': total,
        })

        # Savings
        qs = Saving.objects.month_type_sum(year)
        total_row = H.sum_detailed(qs, 'date', ['sum'])
        total_col = H.sum_detailed(qs, 'title', ['sum'])
        total = sum_col(total_col, 'sum')

        context['data'].append({
            'name': 'Taupymas',
            'data': qs,
            'total_row': total_row,
            'total_col': total_col,
            'total': total,
        })

        # Expenses
        qs = [*Expense.objects.month_name_sum(year)]
        for expense_type in H.expense_types():
            filtered = [*filter(lambda x: expense_type in x['type_title'], qs)]
            total_row = H.sum_detailed(filtered, 'date', ['sum'])
            total_col = H.sum_detailed(filtered, 'title', ['sum'])
            total = sum_col(total_col, 'sum')

            context['data'].append({
                'name': f'Išlaidos / {expense_type}',
                'data': filtered,
                'total_row': total_row,
                'total_col': total_col,
                'total': total,
            })

        return context


def reload_month(request):
    template = 'bookkeeping/includes/reload_month.html'
    ajax_trigger = request.GET.get('ajax_trigger')

    if ajax_trigger:
        context = _month_context(request, {})

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
