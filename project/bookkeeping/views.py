from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.lib.translation import month_names
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import (CreateViewMixin, FormViewMixin,
                                 TemplateViewMixin, httpHtmxResponse,
                                 rendered_content)
from ..pensions.models import PensionType
from ..savings.models import SavingType
from .forms import (AccountWorthForm, DateForm, PensionWorthForm,
                    SavingWorthForm, SummaryExpensesForm)
from .lib.no_incomes import NoIncomes as LibNoIncomes
from .models import AccountWorth, PensionWorth, SavingWorth
from .services.accounts import AccountService
from .services.chart_summary import ChartSummaryService
from .services.chart_summary_expenses import ChartSummaryExpensesService
from .services.detailed import DetailedService
from .services.expand_day import ExpandDayService
from .services.expenses import ExpensesService
from .services.index import IndexService
from .services.month import MonthService
from .services.pensions import PensionsService
from .services.savings import SavingsService
from .services.summary_savings import SummarySavingsService
from .services.wealth import WealthService


class Index(TemplateViewMixin):
    template_name = 'bookkeeping/index.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        ind = IndexService(self.request, year)
        exp = ExpensesService(self.request, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'year': year,
            'accounts': rendered_content(self.request, Accounts, **kwargs),
            'savings': rendered_content(self.request, Savings, **kwargs),
            'pensions': rendered_content(self.request, Pensions, **kwargs),
            'wealth': rendered_content(self.request, Wealth, **kwargs),
            'no_incomes': rendered_content(self.request, NoIncomes, **kwargs),
            'year_balance': ind.render_year_balance(),
            'year_balance_short': ind.render_year_balance_short(),
            'averages': ind.render_averages(),
            'borrow': ind.render_borrow(),
            'lend': ind.render_lend(),
            'chart_balance': ind.render_chart_balance(),
            'chart_expenses': exp.render_chart_expenses(),
            'year_expenses': exp.render_year_expenses(),
        })
        return context


class Accounts(TemplateViewMixin):
    template_name = 'bookkeeping/includes/account_worth_list.html'

    def get_context_data(self, **kwargs):
        obj = AccountService(self.request.user.year)

        context = super().get_context_data(**kwargs)
        context.update({
            'items': obj.data,
            'total_row': obj.total_row,
        })

        return context


class AccountsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm
    shared_form_class = DateForm
    template_name = 'bookkeeping/includes/account_worth_form.html'
    url = reverse_lazy('bookkeeping:accounts_worth_new')
    hx_trigger_django = 'afterAccountWorthNew'


class AccountsWorthReset(TemplateViewMixin):
    account = None

    def get_object(self):
        account = None
        try:
            account = \
                Account.objects \
                .related() \
                .get(pk=self.kwargs['pk'])
        except ObjectDoesNotExist:
            pass

        return account

    def dispatch(self, request, *args, **kwargs):
        self.account = self.get_object()
        worth = None

        if self.account:
            try:
                worth = \
                    AccountWorth.objects \
                    .filter(account=self.account) \
                    .latest('date')
            except ObjectDoesNotExist:
                pass

        worth_price  = worth.price if worth else 0

        if not all((self.account, worth, worth_price)):
            return HttpResponse(status=204)  # 204 - No Content

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        AccountWorth.objects.create(
            price=0,
            account=self.account,
            date=timezone.now()
        )
        return httpHtmxResponse('afterReset')


class Savings(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        obj = SavingsService(self.request.user.year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Funds'),
            'type': 'savings',
            **obj.context()
        })
        return context


class SavingsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm
    shared_form_class = DateForm
    template_name = 'bookkeeping/includes/saving_worth_form.html'
    url = reverse_lazy('bookkeeping:savings_worth_new')
    hx_trigger_django = 'afterSavingWorthNew'


class Pensions(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        obj = PensionsService(self.request.user.year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Pensions'),
            'type': 'pensions',
            'items': obj.data,
            'total_row': obj.total_row,
        })
        return context


class PensionsWorthNew(FormsetMixin, CreateViewMixin):
    type_model = PensionType
    model = PensionWorth
    form_class = PensionWorthForm
    shared_form_class = DateForm
    template_name = 'bookkeeping/includes/pension_worth_form.html'
    url = reverse_lazy('bookkeeping:pensions_worth_new')
    hx_trigger_django = 'afterPensionWorthNew'


class Wealth(TemplateViewMixin):
    template_name = 'bookkeeping/includes/info_table.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        obj = WealthService(year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': [_('Money'), _('Wealth')],
            'data': [obj.money, obj.wealth],
        })
        return context


class NoIncomes(TemplateViewMixin):
    template_name = 'bookkeeping/includes/no_incomes.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        journal = self.request.user.journal

        obj = LibNoIncomes(journal, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'no_incomes': obj.summary,
            'save_sum': obj.cut_sum,
            'not_use': obj.unnecessary,
            'avg_expenses': obj.avg_expenses,
        })

        return context


class Month(TemplateViewMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        if self.request.htmx:
            self.template_name = 'bookkeeping/includes/month_content.html'

        year = self.request.user.year
        month = self.request.user.month

        obj = MonthService(self.request, year, month)

        context = super().get_context_data(**kwargs)
        context.update({
            'month_table': obj.render_month_table(),
            'info': obj.render_info(),
            'chart_expenses': obj.render_chart_expenses(),
            'chart_targets': obj.render_chart_targets(),
        })
        return context


class Detailed(TemplateViewMixin):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = super().get_context_data(**kwargs)
        context['months'] = range(1, 13)
        context['month_names'] = month_names()

        ctx = DetailedService(year)
        ctx.incomes_context(context)
        ctx.savings_context(context)
        ctx.expenses_context(context)

        return context


class Summary(TemplateViewMixin):
    template_name = 'bookkeeping/summary.html'

    def get_context_data(self, **kwargs):
        return \
            ChartSummaryService().context(super().get_context_data(**kwargs))


class SummarySavings(TemplateViewMixin):
    template_name = 'bookkeeping/summary_savings.html'

    def get_context_data(self, **kwargs):
        obj = SummarySavingsService()

        context = super().get_context_data(**kwargs)
        context['records'] = obj.records

        if not obj.records or obj.records < 1:
            return context

        context.update({
            'funds': obj.make_chart_data('funds'),
            'shares': obj.make_chart_data('shares'),
            'funds_shares': obj.make_chart_data('funds', 'shares'),
            'pensions3': obj.make_chart_data('pensions3'),
            'pensions2': obj.make_chart_data('pensions2'),
            'all': obj.make_chart_data('funds', 'shares', 'pensions3'),
        })

        return context


class SummaryExpenses(FormViewMixin):
    form_class = SummaryExpensesForm
    template_name = 'bookkeeping/summary_expenses.html'
    success_url = reverse_lazy('bookkeeping:summary_expenses')

    def form_valid(self, form, **kwargs):
        data = form.cleaned_data.get('types')
        obj = ChartSummaryExpensesService(form_data=data, remove_empty_columns=True)

        context = {'found': False, 'form': form}

        if obj.serries_data:
            context.update({
                'found': True,
                'categories': obj.categories,
                'data': obj.serries_data,
                'total_col': obj.total_col,
                'total_row': obj.total_row,
                'total': obj.total
            })
        else:
            context.update({
                'error': _('No data found')
            })

        return render(self.request, self.template_name, context)


class ExpandDayExpenses(TemplateViewMixin):
    template_name = 'bookkeeping/includes/expand_day_expenses.html'

    def get_context_data(self, **kwargs):
        obj = ExpandDayService(kwargs.get('date'))

        context = super().get_context_data(**kwargs)
        context.update(**obj.context())

        return context
