from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, reverse
from django.views.generic import TemplateView

from ..accounts.models import Account, AccountBalance
from ..core.lib.date import year_month_list
from ..core.lib.utils import sum_all, sum_col
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import PensionBalance, PensionType
from ..savings.models import Saving, SavingBalance, SavingType
from .forms import AccountWorthForm, PensionWorthForm, SavingWorthForm
from .lib import views_helpers as H
from .models import AccountWorth, PensionWorth, SavingWorth


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.year
        obj = H.IndexHelper(self.request, year)

        context['year'] = year
        context['accounts'] = obj.render_accounts()
        context['savings'] = obj.render_savings()
        context['pensions'] = obj.render_pensions()
        context['year_balance'] = obj.render_year_balance()
        context['year_balance_short'] = obj.render_year_balance_short()
        context['year_expenses'] = obj.render_year_expenses()
        context['no_incomes'] = obj.render_no_incomes()
        context['avg_incomes'] = obj.render_avg_incomes()
        context['avg_expenses'] = obj.render_avg_expenses()
        context['money'] = obj.render_money()
        context['wealth'] = obj.render_wealth()
        context['chart_expenses'] = obj.render_chart_expenses()
        context['chart_balance'] = obj.render_chart_balance()

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm
    # list_template_name = 'bookkeeping/includes/worth_table.html'
    list_render_output = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        _fund = SavingBalance.objects.year(year)

        context['title'] = 'Fondai'
        context['items'] = _fund
        context['total_row'] = sum_all(_fund)

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        _account = AccountBalance.objects.year(year)

        context['accounts'] = _account
        context['total_row'] = sum_all(_account)

        return context


class PensionsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = PensionType
    model = PensionWorth
    form_class = PensionWorthForm
    list_template_name = 'bookkeeping/includes/worth_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.year

        _pension = PensionBalance.objects.year(year)

        context['title'] = 'Pensija'
        context['items'] = _pension
        context['total_row'] = sum_all(_pension)

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

        year = self.request.user.year

        context['months'] = range(1, 13)
        context['data'] = []

        def _gen_data(data, name):
            total_row = H.sum_detailed(data, 'date', ['sum'])
            total_col = H.sum_detailed(data, 'title', ['sum'])
            total = sum_col(total_col, 'sum')

            context['data'].append({
                'name': name,
                'data': data,
                'total_row': total_row,
                'total_col': total_col,
                'total': total,
            })

        # Incomes
        qs = Income.objects.month_type_sum(year)
        _gen_data(qs, 'Pajamos')

        # Savings
        qs = Saving.objects.month_type_sum(year)
        _gen_data(qs, 'Taupymas')

        # Expenses
        qs = [*Expense.objects.month_name_sum(year)]
        for i in H.expense_types():
            filtered = filter(lambda x: i in x['type_title'], qs)
            _gen_data([*filtered], f'Išlaidos / {i}')

        return context


def reload_index(request):
    template = 'bookkeeping/includes/reload_index.html'
    ajax_trigger = request.GET.get('ajax_trigger')

    if ajax_trigger:
        year = request.user.year
        obj = H.IndexHelper(request, year)

        context = {
            'no_incomes': obj.render_no_incomes(),
            'money': obj.render_money(),
            'wealth': obj.render_wealth(),
            'savings': obj.render_savings(),
        }
        return render(request, template, context)

    return redirect(reverse('bookkeeping:index'))


def reload_month(request):
    template = 'bookkeeping/includes/reload_month.html'
    ajax_trigger = request.GET.get('ajax_trigger')

    if ajax_trigger:
        context = _month_context(request, {})
        return render(request, template, context)

    return redirect(reverse('bookkeeping:month'))


def _month_context(request, context):
    year = request.user.year
    month = request.user.month

    obj = H.MonthHelper(request, year, month)

    context['month_table'] = obj.render_month_table()
    context['info'] = obj.render_info()
    context['chart_expenses'] = obj.render_chart_expenses()
    context['chart_targets'] = obj.render_chart_targets()

    return context
