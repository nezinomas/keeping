from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Sum
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView

from ..accounts.models import Account
from ..core.lib.transalation import month_names
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, DispatchAjaxMixin, IndexMixin
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import PensionBalance, PensionType
from ..savings.models import Saving, SavingBalance, SavingType
from .forms import AccountWorthForm, PensionWorthForm, SavingWorthForm
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
            'lent': obj.render_lent(),
            'chart_expenses': exp.render_chart_expenses(),
            'chart_balance': obj.render_chart_balance(),
        })
        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm
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
                savings.get('price__sum', 0)
            )
        })
        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm
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
    list_template_name = 'bookkeeping/includes/worth_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.year
        pensions = PensionBalance.objects.year(year)

        context.update({
            **H.IndexHelper.pensions_context(pensions)
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
        H.detailed_context(context, qs, _('Incomes'))

        # Savings
        qs = Saving.objects.sum_by_month_and_type(year)
        H.detailed_context(context, qs, _('Savings'))

        # Expenses
        qs = [*Expense.objects.sum_by_month_and_name(year)]
        expenses_types = H.expense_types()
        for title in expenses_types:
            filtered = filter(lambda x: title in x['type_title'], qs)
            H.detailed_context(context, [*filtered], _('Expenses / %(title)s') % ({'title': title}))

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
            Expense.objects
            .items()
            .filter(date=dt)
            .order_by('expense_type', F('expense_name').asc(), 'price')
        )

        context = {
            'items': items,
            'notice': f'{dt:%F} dieną įrašų nėra',
        }
        template = 'bookkeeping/includes/expand_day_expenses.html'
        html = render_to_string(template, context, request)

        return JsonResponse({'html': html})


class AccountsWorthReset(LoginRequiredMixin, CreateView):
    account = None
    model = Account
    template_name = 'bookkeeping/includes/accounts_worth.html'

    def dispatch(self, request, *args, **kwargs):
        self.account = self.get_object()
        worth = (
            AccountWorth.objects
            .filter(account=self.account)
            .latest('date')
        )

        if worth.price == 0:
            return HttpResponse(status=204)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        AccountWorth.objects.create(price=0, account=self.account)

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
    template_name = 'bookkeeping/includes/reload_month.html'
    redirect_view = reverse_lazy('bookkeeping:month')

    def get(self, request, *args, **kwargs):
        context = H.month_context(request)
        return JsonResponse(context)
