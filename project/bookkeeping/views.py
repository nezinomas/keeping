from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, TemplateView

from ..accounts.models import Account, AccountBalance
from ..core.lib.date import year_month_list
from ..core.lib.utils import sum_all
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
        year = self.request.user.year
        obj = H.IndexHelper(self.request, year)

        context = super().get_context_data(**kwargs)
        context.update({
            'year': year,
            'accounts': obj.render_accounts(),
            'savings': obj.render_savings(),
            'pensions': obj.render_pensions(),
            'year_balance': obj.render_year_balance(),
            'year_balance_short': obj.render_year_balance_short(),
            'year_expenses': obj.render_year_expenses(),
            'no_incomes': obj.render_no_incomes(),
            'avg_incomes': obj.render_avg_incomes(),
            'avg_expenses': obj.render_avg_expenses(),
            'money': obj.render_money(),
            'wealth': obj.render_wealth(),
            'chart_expenses': obj.render_chart_expenses(),
            'chart_balance': obj.render_chart_balance(),
        })
        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm
    list_render_output = False

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        fund = SavingBalance.objects.year(year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Fondai',
            'items': fund,
            'total_row': sum_all(fund),
        })
        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        account = AccountBalance.objects.year(year)

        context = super().get_context_data(**kwargs)
        context.update({
            'accounts': account,
            'total_row': sum_all(account),
        })
        return context


class PensionsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = PensionType
    model = PensionWorth
    form_class = PensionWorthForm
    list_template_name = 'bookkeeping/includes/worth_table.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        pension = PensionBalance.objects.year(year)

        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Pensija',
            'items': pension,
            'total_row': sum_all(pension),
        })
        return context


class Month(IndexMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'buttons': year_month_list(),
            **H.month_context(self.request, context),
        })
        return context


class Detailed(LoginRequiredMixin, TemplateView):
    template_name = 'bookkeeping/detailed.html'

    def get_context_data(self, **kwargs):
        year = self.request.user.year

        context = super().get_context_data(**kwargs)
        context['months'] = range(1, 13)

        # Incomes
        qs = Income.objects.sum_by_month_and_type(year)
        H.detailed_context(context, qs, 'Pajamos')

        # Savings
        qs = Saving.objects.sum_by_month_and_type(year)
        H.detailed_context(context, qs, 'Taupymas')

        # Expenses
        qs = [*Expense.objects.sum_by_month_and_name(year)]
        expenses_types = H.expense_types()
        for title in expenses_types:
            filtered = filter(lambda x: title in x['type_title'], qs)
            H.detailed_context(context, [*filtered], f'Išlaidos / {title}')

        return context


class Summary(LoginRequiredMixin, TemplateView):
    template_name = 'bookkeeping/summary.html'

    def get_context_data(self, **kwargs):
        offset = 1.2
        context = super().get_context_data(**kwargs)

        # data for balance summary
        qs_inc = Income.objects.sum_by_year()
        qs_exp = Expense.objects.sum_by_year()

        balance_years = [x['year'] for x in qs_exp]

        context.update({
            'balance_categories': balance_years,
            'balance_income_data': [float(x['sum']) for x in qs_inc],
            'balance_income_avg': H.average(qs_inc),
            'balance_expense_data': [float(x['sum']) for x in qs_exp],
            'balance_cnt': len(balance_years) - offset,
        })

        # data for salary summary
        qs = list(Income.objects.sum_by_year(['Atlyginimas', 'Premijos']))
        salary_years = [x['year'] for x in qs]

        context.update({
            'salary_categories': salary_years,
            'salary_data_avg': H.average(qs),
            'salary_cnt': len(salary_years) - offset,
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
    template_name = 'bookkeeping/includes/reload_index.html'

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
        context = {'accounts': obj.render_accounts()}

        return self.render_to_response(context)


def reload_index(request):
    try:
        request.GET['ajax_trigger']
    except KeyError:
        return redirect(reverse('bookkeeping:index'))

    obj = H.IndexHelper(request, request.user.year)
    context = {
        'no_incomes': obj.render_no_incomes(),
        'money': obj.render_money(),
        'wealth': obj.render_wealth(),
        'savings': obj.render_savings(),
    }

    return render(
        request=request,
        template_name='bookkeeping/includes/reload_index.html',
        context=context
    )


def reload_month(request):
    try:
        request.GET['ajax_trigger']
    except KeyError:
        return redirect(reverse('bookkeeping:month'))

    return render(
        request=request,
        template_name='bookkeeping/includes/reload_month.html',
        context=H.month_context(request))
