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

from ..accounts.models import Account
from ..core.lib import utils
from ..core.lib.date import years
from ..core.lib.transalation import month_names
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.get import GetQuerysetMixin
from ..core.mixins.views import CreateAjaxMixin, DispatchAjaxMixin, IndexMixin
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import PensionBalance, PensionType
from ..savings.models import Saving, SavingBalance, SavingType
from .forms import (AccountWorthForm, DateForm, PensionWorthForm,
                    SavingWorthForm, SummaryExpensesForm)
from .lib import summary_view_helper as SH
from .lib import views_helpers as H
from .models import AccountWorth, PensionWorth, SavingWorth


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        year = self.request.user.year
        obj = H.IndexHelper(self.request, year)
        exp = H.ExpensesHelper(self.request, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'year': year,
            'accounts': obj.render_accounts(),
            'savings': obj.render_savings(),
            'pensions': obj.render_pensions(),
            'year_balance': obj.render_year_balance(),
            'year_balance_short': obj.render_year_balance_short(),
            'year_expenses': exp.render_year_expenses(),
            'no_incomes': obj.render_no_incomes(),
            'averages': obj.render_averages(),
            'wealth': obj.render_wealth(),
            'borrow': obj.render_borrow(),
            'debt': obj.render_debt(),
            'chart_expenses': exp.render_chart_expenses(),
            'chart_balance': obj.render_chart_balance(),
        })
        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm
    shared_form_class = DateForm
    list_template_name = 'bookkeeping/includes/worth_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.year
        funds = SavingBalance.objects.year(year)
        incomes = Income.objects.year(year).aggregate(Sum('price'))
        savings = Saving.objects.year(year).aggregate(Sum('price'))

        context.update({
            **H.IndexHelper.savings_context(
                funds,
                incomes.get('price__sum', 0),
                savings.get('price__sum', 0),
                year
            )
        })
        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm
    shared_form_class = DateForm
    list_template_name = 'bookkeeping/includes/accounts_worth_list.html'

    def get_context_data(self, **kwargs):
        obj = H.IndexHelper(self.request, self.request.user.year)

        context = super().get_context_data(**kwargs)
        context.update({**obj.render_accounts(to_string=False)})

        return context


class PensionsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = PensionType
    model = PensionWorth
    form_class = PensionWorthForm
    shared_form_class = DateForm
    list_template_name = 'bookkeeping/includes/worth_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.year
        pensions = PensionBalance.objects.year(year)

        context.update({
            **H.IndexHelper.pensions_context(pensions, year)
        })

        return context


class Month(IndexMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            **H.month_context(self.request, context),
        })
        return context


class Detailed(IndexMixin):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = super().get_context_data(**kwargs)
        context['months'] = range(1, 13)
        context['month_names'] = month_names()

        # Incomes
        qs = Income.objects.sum_by_month_and_type(year)
        if qs.exists():
            H.detailed_context(context, qs, _('Incomes'))

        # Savings
        qs = Saving.objects.sum_by_month_and_type(year)
        if qs.exists():
            H.detailed_context(context, qs, _('Savings'))

        # Expenses
        qs = [*Expense.objects.sum_by_month_and_name(year)]
        expenses_types = H.expense_types()
        for title in expenses_types:
            filtered = [*filter(lambda x: title in x['type_title'], qs)]

            if not filtered:
                continue

            H.detailed_context(
                context=context,
                data=filtered,
                name=_('Expenses / %(title)s') % ({'title': title})
            )

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
            'balance_income_avg': H.average(qs_inc),
            'balance_expense_data': [float(x['sum']) for x in qs_exp],
        })

        # data for salary summary
        qs = list(Income.objects.sum_by_year(['salary']))
        salary_years = [x['year'] for x in qs]

        context.update({
            'salary_categories': salary_years,
            'salary_data_avg': H.average(qs),
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

        context['funds'] = SH.chart_data(funds)
        context['shares'] = SH.chart_data(shares)
        context['funds_shares'] = SH.chart_data(funds, shares)
        context['pensions3'] = SH.chart_data(pensions3)
        context['pensions2'] = SH.chart_data(PensionBalance.objects.sum_by_year())
        context['all'] = SH.chart_data(funds, shares, pensions3)

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
        self.form_data_dict = SH.make_form_data_dict(self.form_data)

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

        obj = SH.ExpenseCompareHelper(
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


class ExpandDayExpenses(IndexMixin):
    def get(self, request, *args, **kwargs):
        try:
            _date = kwargs.get('date')
            _year = int(_date[:4])
            _month = int(_date[4:6])
            _day = int(_date[6:8])
            dt = datetime(_year, _month, _day)
        except Exception:  # pylint: disable=broad-except
            dt = datetime(1970, 1, 1)

        items = (
            Expense
            .objects
            .items()
            .filter(date=dt)
            .order_by('expense_type', F('expense_name').asc(), 'price')
        )

        context = {
            'items': items,
            'notice': _('No records on day %(day)s') % ({'day': f'{dt:%F}'}),
        }
        template = 'bookkeeping/includes/expand_day_expenses.html'
        html = render_to_string(template, context, request)

        return JsonResponse({'html': html})


class AccountsWorthReset(LoginRequiredMixin, GetQuerysetMixin, CreateView):
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
            return HttpResponse(status=204) # 204 - No Content

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        AccountWorth.objects.create(
            price=0,
            account=self.account,
            date=timezone.now()
        )

        obj = H.IndexHelper(request, request.user.year)
        context = {'accounts_worth': obj.render_accounts()}

        return JsonResponse(context)


class ReloadIndex(DispatchAjaxMixin, IndexMixin):
    template_name = 'bookkeeping/index.html'
    redirect_view = reverse_lazy('bookkeeping:index')

    def get(self, request, *args, **kwargs):
        obj = H.IndexHelper(request, request.user.year)
        context = {
            'no_incomes': obj.render_no_incomes(),
            'wealth': obj.render_wealth(to_string=True),
        }
        return JsonResponse(context)


class ReloadMonth(DispatchAjaxMixin, IndexMixin):
    template_name = 'bookkeeping/includes/month.html'
    redirect_view = reverse_lazy('bookkeeping:month')

    def get(self, request, *args, **kwargs):
        context = H.month_context(request)
        return JsonResponse(context)
