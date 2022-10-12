from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib.translation import month_names
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import (CreateViewMixin, FormViewMixin,
                                 TemplateViewMixin, rendered_content)
from ..pensions.models import PensionType
from ..savings.models import SavingType
from . import forms, mixins, models, services
from .lib.no_incomes import NoIncomes as LibNoIncomes


class Index(TemplateViewMixin):
    template_name = 'bookkeeping/index.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        ind = services.IndexService(year)
        exp = services.ExpenseService(year)

        context = {
            'year': year,
            'accounts': rendered_content(self.request, Accounts, **kwargs),
            'savings': rendered_content(self.request, Savings, **kwargs),
            'pensions': rendered_content(self.request, Pensions, **kwargs),
            'wealth': rendered_content(self.request, Wealth, **kwargs),
            'no_incomes': rendered_content(self.request, NoIncomes, **kwargs),
            'averages': ind.averages_context(),
            'borrow': ind.borrow_context(),
            'lend': ind.lend_context(),
            'balance_short': ind.balance_short_context(),
            'balance': render_to_string(
                'bookkeeping/includes/year_balance.html',
                ind.balance_context(),
                self.request),
            'chart_balance': ind.chart_balance_context(),
            'chart_expenses': exp.chart_context(),
            'expenses': render_to_string(
                'bookkeeping/includes/year_expenses.html',
                exp.table_context(),
                self.request)
        }
        return super().get_context_data(**kwargs) | context


class Accounts(TemplateViewMixin):
    template_name = 'bookkeeping/includes/account_worth_list.html'

    def get_context_data(self, **kwargs):
        obj = services.AccountService(self.request.user.year)

        context = {
            'items': obj.data,
            'total_row': obj.total_row,
        }
        return super().get_context_data(**kwargs) | context


class AccountsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = Account
    model = models.AccountWorth
    form_class = forms.AccountWorthForm
    shared_form_class = forms.DateForm
    template_name = 'bookkeeping/includes/account_worth_form.html'
    url = reverse_lazy('bookkeeping:accounts_worth_new')
    hx_trigger_django = 'afterAccountWorthNew'


class AccountsWorthReset(mixins.AccountWorthResetMixin):
    pass


class Savings(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        obj = services.SavingsService(self.request.user.year)

        context = {
            'title': _('Funds'),
            'type': 'savings',
            **obj.context()
        }
        return super().get_context_data(**kwargs) | context


class SavingsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = SavingType
    model = models.SavingWorth
    form_class = forms.SavingWorthForm
    shared_form_class = forms.DateForm
    template_name = 'bookkeeping/includes/saving_worth_form.html'
    url = reverse_lazy('bookkeeping:savings_worth_new')
    hx_trigger_django = 'afterSavingWorthNew'


class Pensions(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        obj = services.PensionsService(self.request.user.year)

        context = {
            'title': _('Pensions'),
            'type': 'pensions',
            'items': obj.data,
            'total_row': obj.total_row,
        }
        return super().get_context_data(**kwargs) | context


class PensionsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = PensionType
    model = models.PensionWorth
    form_class = forms.PensionWorthForm
    shared_form_class = forms.DateForm
    template_name = 'bookkeeping/includes/pension_worth_form.html'
    url = reverse_lazy('bookkeeping:pensions_worth_new')
    hx_trigger_django = 'afterPensionWorthNew'


class Wealth(TemplateViewMixin):
    template_name = 'bookkeeping/includes/info_table.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        obj = services.WealthService(year)

        context = {
            'title': [_('Money'), _('Wealth')],
            'data': [obj.money, obj.wealth],
        }
        return super().get_context_data(**kwargs) | context


class NoIncomes(TemplateViewMixin):
    template_name = 'bookkeeping/includes/no_incomes.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        journal = self.request.user.journal

        obj = LibNoIncomes(journal, year)

        context = {
            'no_incomes': obj.summary,
            'save_sum': obj.cut_sum,
            'not_use': obj.unnecessary,
            'avg_expenses': obj.avg_expenses,
        }
        return super().get_context_data(**kwargs) | context


class Month(TemplateViewMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        if self.request.htmx:
            self.template_name = 'bookkeeping/includes/month_content.html'

        year = self.request.user.year
        month = self.request.user.month

        obj = services.MonthService(year, month)

        context = {
            'month_table': render_to_string(
                'bookkeeping/includes/month_table.html',
                obj.month_table_context(),
                self.request),
            'info': render_to_string(
                'bookkeeping/includes/spending_info.html',
                {'items': obj.info_context},
                self.request),
            'chart_expenses': render_to_string(
                'bookkeeping/includes/chart_month_expenses.html',
                obj.chart_expenses_context(),
                self.request),
            'chart_targets': render_to_string(
                'bookkeeping/includes/chart_month_targets.html',
                obj.chart_targets_context(),
                self.request),
        }
        return super().get_context_data(**kwargs) | context


class Detailed(TemplateViewMixin):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = {
            'months': range(1, 13),
            'month_names': month_names(),
        }

        ctx = services.DetailedService(year)

        ctx.incomes_context(context)
        ctx.savings_context(context)
        ctx.expenses_context(context)

        return super().get_context_data(**kwargs) | context


class Summary(TemplateViewMixin):
    template_name = 'bookkeeping/summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return \
            services.ChartSummaryService().context(context)


class SummarySavings(TemplateViewMixin):
    template_name = 'bookkeeping/summary_savings.html'

    def get_context_data(self, **kwargs):
        obj = services.SummarySavingsService()

        context = super().get_context_data(**kwargs)
        context['records'] = obj.records

        if not obj.records or obj.records < 1:
            return context

        context |= {
            'funds': obj.make_chart_data('funds'),
            'shares': obj.make_chart_data('shares'),
            'funds_shares': obj.make_chart_data('funds', 'shares'),
            'pensions3': obj.make_chart_data('pensions3'),
            'pensions2': obj.make_chart_data('pensions2'),
            'all': obj.make_chart_data('funds', 'shares', 'pensions3'),
        }

        return context


class SummaryExpenses(FormViewMixin):
    form_class = forms.SummaryExpensesForm
    template_name = 'bookkeeping/summary_expenses.html'
    success_url = reverse_lazy('bookkeeping:summary_expenses')

    def form_valid(self, form, **kwargs):
        data = form.cleaned_data.get('types')
        obj = services.ChartSummaryExpensesService(form_data=data,
                                                   remove_empty_columns=True)

        context = {'found': False, 'form': form}

        if obj.serries_data:
            context |= {
                'found': True,
                'categories': obj.categories,
                'data': obj.serries_data,
                'total_col': obj.total_col,
                'total_row': obj.total_row,
                'total': obj.total
            }
        else:
            context['error'] = _('No data found')

        return render(self.request, self.template_name, context)


class ExpandDayExpenses(TemplateViewMixin):
    template_name = 'bookkeeping/includes/expand_day_expenses.html'

    def get_context_data(self, **kwargs):
        obj = services.ExpandDayService(kwargs.get('date'))

        return super().get_context_data(**kwargs) | obj.context()
