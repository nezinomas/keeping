from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Sum
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView

from ..accounts.models import Account, AccountBalance
from ..core.lib import utils
from ..core.lib.date import years
from ..core.lib.translation import month_names
from ..core.lib.utils import sum_all
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import (CreateAjaxMixin, CreateViewMixin,
                                 DeleteViewMixin, DispatchAjaxMixin,
                                 FormViewMixin, IndexMixin, ListViewMixin,
                                 RedirectViewMixin, TemplateViewMixin,
                                 UpdateViewMixin, rendered_content)
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import PensionBalance, PensionType
from ..savings.models import Saving, SavingBalance, SavingType
from .forms import (AccountWorthForm, DateForm, PensionWorthForm,
                    SavingWorthForm, SummaryExpensesForm)
from .lib import summary_view_helper as SummaryViewHelper
from .lib import views_helpers as Helper
from .lib.no_incomes import NoIncomes as LibNoIncomes
from .lib.views_helpers import (DetailedHelper, ExpensesHelper, IndexHelper,
                                MonthHelper)
from .models import AccountWorth, PensionWorth, SavingWorth


class Index(TemplateViewMixin):
    template_name = 'bookkeeping/index.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        obj = IndexHelper(self.request, year)
        exp = ExpensesHelper(self.request, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'year': year,
            'accounts': rendered_content(self.request, Accounts, **kwargs),
            'savings': rendered_content(self.request, Savings, **kwargs),
            'pensions': rendered_content(self.request, Pensions, **kwargs),
            'wealth': rendered_content(self.request, Wealth, **kwargs),
            'no_incomes': rendered_content(self.request, NoIncomes, **kwargs),
            'year_balance': obj.render_year_balance(),
            'year_balance_short': obj.render_year_balance_short(),
            'year_expenses': exp.render_year_expenses(),
            'averages': obj.render_averages(),
            'borrow': obj.render_borrow(),
            'lend': obj.render_lend(),
            'chart_expenses': exp.render_chart_expenses(),
            'chart_balance': obj.render_chart_balance(),
        })
        return context


class Accounts(TemplateViewMixin):
    template_name = 'bookkeeping/includes/account_worth_list.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        qs = AccountBalance.objects.year(year)

        Helper.add_latest_check_key(AccountWorth, qs, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'items': qs,
            'total_row': sum_all(qs),
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


class AccountsWorthReset(LoginRequiredMixin, CreateView):
    account = None
    model = Account
    template_name = 'bookkeeping/includes/accounts_worth.html'

    def dispatch(self, request, *args, **kwargs):
        self.account = self.get_object()
        if self.account:
            try:
                worth = (
                    AccountWorth
                    .objects
                    .filter(account=self.account)
                    .latest('date')
                )
            except ObjectDoesNotExist:
                worth = None

        if not self.account or not worth or worth.price == 0:
            return HttpResponse(status=204)  # 204 - No Content

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        AccountWorth.objects.create(
            price=0,
            account=self.account,
            date=timezone.now()
        )

        obj = IndexHelper(request, request.user.year)
        context = {'accounts_worth': obj.render_accounts()}

        return JsonResponse(context)


class Savings(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        sum_incomes = Income.objects.year(year).aggregate(Sum('price'))['price__sum']

        savings = SavingBalance.objects.year(year)
        total_row = sum_all(savings)
        sum_savings = total_row.get('invested', 0) - total_row.get('past_amount', 0)

        Helper.add_latest_check_key(SavingWorth, savings, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Funds'),
            'items': savings,
            'total_row': total_row,
            'percentage_from_incomes': (
                IndexHelper.percentage_from_incomes(float(sum_incomes), sum_savings)
            ),
            'profit_incomes_proc': (
                IndexHelper.percentage_from_incomes(
                    total_row.get('incomes'),
                    total_row.get('market_value')
                ) - 100
            ),
            'profit_invested_proc': (
                IndexHelper.percentage_from_incomes(
                    total_row.get('invested'),
                    total_row.get('market_value')
                ) - 100
            ),
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
        year = self.request.user.year
        pensions = PensionBalance.objects.year(year)

        Helper.add_latest_check_key(PensionWorth, pensions, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Pensions'),
            'items': pensions,
            'total_row': sum_all(pensions),
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
        account_sum = \
            AccountBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('balance'))['balance__sum']
        fund_sum = \
            SavingBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('market_value'))['market_value__sum']
        pension_sum = \
            PensionBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('market_value'))['market_value__sum']

        money = account_sum + fund_sum
        wealth = account_sum + fund_sum + pension_sum

        context = super().get_context_data(**kwargs)
        context.update({
            'title': [_('Money'), _('Wealth')],
            'data': [money, wealth],
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

        obj = MonthHelper(self.request, year, month)

        context = super().get_context_data(**kwargs)
        context.update({
            'month_table': obj.render_month_table(),
            'info': obj.render_info(),
            'chart_expenses': obj.render_chart_expenses(),
            'chart_targets': obj.render_chart_targets(),
        })
        return context


class Detailed(IndexMixin):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = super().get_context_data(**kwargs)
        context['months'] = range(1, 13)
        context['month_names'] = month_names()

        ctx = DetailedHelper(year)
        ctx.incomes_context(context)
        ctx.savings_context(context)
        ctx.expenses_context(context)

        return context


class Summary(IndexMixin):
    template_name = 'bookkeeping/summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # data for balance summary
        qs_inc = Income.objects.sum_by_year()
        qs_exp = Expense.objects.sum_by_year()

        # generae balance_categories
        _arr = qs_inc if qs_inc else qs_exp
        balance_years = [x['year'] for x in _arr]

        records = len(balance_years)
        context['records'] = records

        if not records or records < 1:
            return context

        context.update({
            'balance_categories': balance_years,
            'balance_income_data': [float(x['sum']) for x in qs_inc],
            'balance_income_avg': Helper.average(qs_inc),
            'balance_expense_data': [float(x['sum']) for x in qs_exp],
        })

        # data for salary summary
        qs = list(Income.objects.sum_by_year(['salary']))
        salary_years = [x['year'] for x in qs]

        context.update({
            'salary_categories': salary_years,
            'salary_data_avg': Helper.average(qs),
        })
        return context


class SummarySavings(IndexMixin):
    template_name = 'bookkeeping/summary_savings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qs = SavingBalance.objects.sum_by_type()

        records = qs.count()
        context['records'] = records

        if not records or records < 1:
            return context

        funds = qs.filter(type='funds')
        shares = qs.filter(type='shares')
        pensions3 = qs.filter(type='pensions')

        context['funds'] = SummaryViewHelper.chart_data(funds)
        context['shares'] = SummaryViewHelper.chart_data(shares)
        context['funds_shares'] = SummaryViewHelper.chart_data(funds, shares)
        context['pensions3'] = SummaryViewHelper.chart_data(pensions3)
        context['pensions2'] = SummaryViewHelper.chart_data(PensionBalance.objects.sum_by_year())
        context['all'] = SummaryViewHelper.chart_data(funds, shares, pensions3)

        return context


class SummaryExpenses(IndexMixin):
    template_name = 'bookkeeping/summary_expenses.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form': SummaryExpensesData.as_view()(self.request, as_string=True)
        })

        return context


class SummaryExpensesData(AjaxSearchMixin):
    url = reverse_lazy('bookkeeping:summary_expenses_data')
    template_name = 'bookkeeping/includes/summary_expenses_form.html'
    form_class = SummaryExpensesForm
    form_data_dict = {}

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_form(self.get_context_data())

        if not utils.is_ajax(self.request):
            return HttpResponse(render_to_string('srsly.html'))

        return super().dispatch(request, *args, **kwargs)

    def make_form_data_dict(self):
        self.form_data_dict = SummaryViewHelper.make_form_data_dict(self.form_data)

    def form_valid(self, form, **kwargs):
        _types = self.form_data_dict['types']
        _names = self.form_data_dict['names']
        _types_qs = None
        _names_qs = None

        if _types:
            _types_qs = Expense.objects.sum_by_year_type(_types)

        if _names:
            _list = _names.split(',')
            _names_qs = Expense.objects.sum_by_year_name(_list)

        obj = SummaryViewHelper.ExpenseCompareHelper(
            years=years()[:-1],
            types=_types_qs,
            names=_names_qs,
            remove_empty_columns=True
        )

        if obj.serries_data:
            context = {
                'categories': obj.categories,
                'data': obj.serries_data,
                'total_col': obj.total_col,
                'total_row': obj.total_row,
                'total': obj.total
            }

            kwargs.update({
                'html': render_to_string(
                    'bookkeeping/includes/summary_expenses_chart.html',
                    context,
                    self.request),
                'html2': render_to_string(
                    'bookkeeping/includes/summary_expenses_table.html',
                    context,
                    self.request),
            })

        return super().form_valid(form, **kwargs)


class ExpandDayExpenses(TemplateViewMixin):
    template_name = 'bookkeeping/includes/expand_day_expenses.html'

    def get_context_data(self, **kwargs):

        try:
            _date = kwargs.get('date')
            _year = int(_date[:4])
            _month = int(_date[4:6])
            _day = int(_date[6:8])
            dt = datetime(_year, _month, _day)
        except ValueError:
            _year, _month, _day = 1970, 1, 1

        dt = datetime(_year, _month, _day)

        object_list = (
            Expense
            .objects
            .items()
            .filter(date=dt)
            .order_by('expense_type', F('expense_name').asc(), 'price')
        )

        context = super().get_context_data(**kwargs)
        context.update({
            'day': _day,
            'object_list': object_list,
            'notice': _('No records on day %(day)s') % ({'day': f'{dt:%F}'}),
        })

        return context
