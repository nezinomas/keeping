from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _

from ..accounts.models import Account, AccountBalance
from ..core.lib.date import years
from ..core.lib.translation import month_names
from ..core.lib.utils import sum_all
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import (CreateViewMixin, FormViewMixin,
                                 TemplateViewMixin, rendered_content, httpHtmxResponse)
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import PensionBalance, PensionType
from ..savings.models import SavingBalance, SavingType
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

        total_row = {
            'past': 0,
            'incomes': 0,
            'expenses': 0,
            'balance': 0,
            'have': 0,
            'delta': 0,
        }

        if qs:
            total_row = sum_all(qs)

        context = super().get_context_data(**kwargs)
        context.update({
            'items': qs,
            'total_row': total_row,
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
        return httpHtmxResponse('afterReset')


class Savings(TemplateViewMixin):
    template_name = 'bookkeeping/includes/funds_table.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        sum_incomes = Income.objects.year(year).aggregate(Sum('price'))['price__sum']
        sum_incomes = float(sum_incomes) if sum_incomes else 0

        savings = SavingBalance.objects.year(year)
        total_row = sum_all(savings)
        sum_savings = total_row.get('invested', 0) - total_row.get('past_amount', 0)

        Helper.add_latest_check_key(SavingWorth, savings, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Funds'),
            'type': 'savings',
            'items': savings,
            'total_row': total_row,
            'percentage_from_incomes': (
                IndexHelper.percentage_from_incomes(sum_incomes, sum_savings)
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
            'type': 'pensions',
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
        account_sum = float(account_sum) if account_sum else 0

        fund_sum = \
            SavingBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('market_value'))['market_value__sum']
        fund_sum = float(fund_sum) if fund_sum else 0

        pension_sum = \
            PensionBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('market_value'))['market_value__sum']
        pension_sum = float(pension_sum) if pension_sum else 0

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


class Detailed(TemplateViewMixin):
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


class Summary(TemplateViewMixin):
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


class SummarySavings(TemplateViewMixin):
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


class SummaryExpenses(FormViewMixin):
    form_class = SummaryExpensesForm
    template_name = 'bookkeeping/summary_expenses.html'
    success_url = reverse_lazy('bookkeeping:summary_expenses')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'found': False,
        })
        return context

    def form_valid(self, form, **kwargs):
        context = {'found': False, 'form': form}
        _types = []
        _names = []
        _types_full = form.cleaned_data.get('types')

        for x in _types_full:
            if ':' in x:
                _names.append(x.split(':')[1])
            else:
                _types.append(x)

        _types_qs = None
        _names_qs = None

        if _types:
            _types_qs = Expense.objects.sum_by_year_type(_types)

        if _names:
            _names_qs = Expense.objects.sum_by_year_name(_names)

        if _types_qs or _names_qs:
            obj = SummaryViewHelper.ExpenseCompareHelper(
                years=years()[:-1],
                types=_types_qs,
                names=_names_qs,
                remove_empty_columns=True
            )

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
