from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from project.bookkeeping.services.month import MonthServiceData

from ..accounts.models import Account
from ..core.lib.translation import month_names
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import (CreateViewMixin, FormViewMixin,
                                 TemplateViewMixin, rendered_content)
from ..pensions.models import PensionType
from ..plans.lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData
from ..savings.models import SavingType
from . import forms, models, services
from .lib.day_spending import DaySpending
from .lib.expense_balance import ExpenseBalance
from .lib.no_incomes import NoIncomes as LibNoIncomes
from .lib.no_incomes import NoIncomesData
from .lib.year_balance import YearBalance


class Index(TemplateViewMixin):
    template_name = 'bookkeeping/index.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        # index service
        data = services.IndexServiceData(year)
        year_balance = YearBalance(
            year=year,
            data=data.data,
            amount_start=data.amount_start)

        ind = services.IndexService(year_balance)

        # expenses service
        data = services.ExpenseServiceData(year)
        balance = ExpenseBalance.months_of_year(
            year=year, expenses=data.expenses, types=data.expense_types)
        exp = services.ExpenseService(data=balance)

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
            'balance': ind.balance_context(),
            'chart_balance': ind.chart_balance_context(),
            'chart_expenses': exp.chart_context(),
            'expenses': exp.table_context(),
        }

        return super().get_context_data(**kwargs) | context


class Accounts(TemplateViewMixin):
    template_name = 'bookkeeping/includes/account_worth_list.html'

    def get_context_data(self, **kwargs):
        data = services.AccountServiceData(self.request.user.year)
        obj = services.AccountService(data=data)

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


class Savings(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        data = services.SavingServiceData(self.request.user.year)
        obj = services.SavingsService(data)

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
        data = services.PensionServiceData(self.request.user.year)
        obj = services.PensionsService(data)

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
        data = services.WealthServiceData(year)
        service = services.WealthService(data)

        context = {
            'title': [_('Money'), _('Wealth')],
            'data': [service.money, service.wealth],
        }
        return super().get_context_data(**kwargs) | context


class NoIncomes(TemplateViewMixin):
    template_name = 'bookkeeping/includes/no_incomes.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        journal = self.request.user.journal
        data = NoIncomesData(
            year=year,
            unnecessary_expenses=journal.unnecessary_expenses,
            unnecessary_savings=journal.unnecessary_savings)
        service = LibNoIncomes(data)

        context = {
            'no_incomes': service.summary,
            'save_sum': service.cut_sum,
            'not_use': service.unnecessary,
            'avg_expenses': service.avg_expenses,
        }
        return super().get_context_data(**kwargs) | context


class Month(TemplateViewMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        if self.request.htmx:
            self.template_name = 'bookkeeping/includes/month_content.html'

        year = self.request.user.year
        month = self.request.user.month
        data = MonthServiceData(year, month)
        plans = PlanCalculateDaySum(PlanCollectData(year, month))
        spending = DaySpending(
            year=data.year,
            month=data.month,
            expenses=data.expenses,
            types=data.expense_types,
            necessary=data.necessary_expense_types,
            day_input=plans.day_input,
            expenses_free=plans.expenses_free
        )
        savings = ExpenseBalance.days_of_month(
            year=data.year,
            month=data.month,
            expenses=data.savings,
            types=[_('Savings')]
        )
        service = services.MonthService(
            data=data,
            plans=plans,
            savings=savings,
            spending=spending
        )
        context = {
            'month_table': service.month_table_context(),
            'info': service.info_context(),
            'chart_expenses': service.chart_expenses_context(),
            'chart_targets': service.chart_targets_context(),
        }
        return super().get_context_data(**kwargs) | context


class Detailed(TemplateViewMixin):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = {
            'month_names': month_names(),
            'data': [],
        }

        data = services.DetailerServiceData(year)
        ctx = services.DetailedService(data)

        context['data'] += ctx.incomes_context()
        context['data'] += ctx.savings_context()
        context['data'] += ctx.expenses_context()

        return super().get_context_data(**kwargs) | context


class Summary(TemplateViewMixin):
    template_name = 'bookkeeping/summary.html'

    def get_context_data(self, **kwargs):
        data = services.ChartSummaryServiceData()
        obj = services.ChartSummaryService(data)

        return {
            'chart_balance': obj.chart_balance(),
            'chart_incomes': obj.chart_incomes()
        }


class SummarySavings(TemplateViewMixin):
    template_name = 'bookkeeping/summary_savings.html'

    def get_context_data(self, **kwargs):
        data = services.SummarySavingsServiceData()
        obj = services.SummarySavingsService(data)

        super_context = super().get_context_data(**kwargs)
        context = dict(records=obj.records)
        if not obj.records or obj.records < 1:
            return super_context | context

        context |= dict(
            funds=
                obj.make_chart_data('funds')
                | dict(chart_title=_('Funds')),
            shares=
                obj.make_chart_data('shares')
                | dict(chart_title=_('Shares')),
            funds_shares=
                obj.make_chart_data('funds', 'shares')
                | dict(chart_title=f"{_('Funds')} {_('Shares')}"),
            pensions3=
                obj.make_chart_data('pensions3')
                | dict(chart_title=f"{_('Pensions')} III"),
            pensions2=
                obj.make_chart_data('pensions2')
                | dict(chart_title=f"{_('Pensions')} II"),
            all=
                obj.make_chart_data('funds', 'shares', 'pensions3')
                | dict(chart_title=f"{_('Funds')}, {_('Shares')}, {_('Pensions')}"),
        )

        return super_context | context


class SummaryExpenses(FormViewMixin):
    form_class = forms.SummaryExpensesForm
    template_name = 'bookkeeping/summary_expenses.html'
    success_url = reverse_lazy('bookkeeping:summary_expenses')

    def form_valid(self, form, **kwargs):
        form_data = form.cleaned_data.get('types')
        data = services.ChartSummaryExpensesServiceData(form_data)
        obj = services.ChartSummaryExpensesService(data=data)

        context = {'found': False, 'form': form}

        if obj.serries_data:
            context |= {
                'found': True,
                'total_col': obj.total_col,
                'total_row': obj.total_row,
                'total': obj.total,
                'chart': {
                    'categories': obj.categories,
                    'data': obj.serries_data,
                }
            }
        else:
            context['error'] = _('No data found')

        return render(self.request, self.template_name, context)


class ExpandDayExpenses(TemplateViewMixin):
    template_name = 'bookkeeping/includes/expand_day_expenses.html'

    def get_context_data(self, **kwargs):
        obj = services.ExpandDayService(kwargs.get('date'))

        return super().get_context_data(**kwargs) | obj.context()
