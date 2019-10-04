from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin

from ..accounts.models import Account
from ..expenses.models import Expense, ExpenseType
from ..incomes.models import Income
from ..savings.models import Saving, SavingType
from ..plans.lib.calc_day_sum import CalcDaySum
from ..plans.models import DayPlan
from ..transactions.models import SavingClose

from ..core.lib.utils import get_value_from_dict
from .lib import views_helpers
from .lib.day_spending import DaySpending
from .lib.expense_stats import MonthExpenseType, MonthsExpenseType
from ..core.lib.date import year_month_list, current_day
from .lib.months_balance import MonthsBalance
from .lib.no_incomes import NoIncomes

from .forms import AccountWorthForm, SavingWorthForm
from .models import AccountWorth, SavingWorth


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        _account = views_helpers.account_stats(year)
        _fund, _pension = views_helpers.saving_stats(year)
        _expense_types = views_helpers.expense_types('Taupymas')

        qs_income = Income.objects.income_sum(year)
        qs_expense = Expense.objects.month_expense(year)
        qs_savings = Saving.objects.month_saving(year)
        qs_savings_close = SavingClose.objects.month_sum(year)
        qs_ExpenseType = Expense.objects.month_expense_type(year)

        _MonthsBalance = MonthsBalance(
            year=year, incomes=qs_income, expenses=qs_expense,
            savings=qs_savings, savings_close=qs_savings_close,
            amount_start=_account.balance_start)

        _MonthsExpenseType = MonthsExpenseType(
            year, qs_ExpenseType, **{'Taupymas': qs_savings})

        _NoIncomes = NoIncomes(
            money=_MonthsBalance.amount_end,
            fund=_fund.total_market,
            pension=_pension.total_market,
            avg_expenses=_MonthsBalance.avg_expenses,
            avg_type_expenses=_MonthsExpenseType.average,
            not_use=['Darbas', 'Laisvalaikis', 'Paskolos', 'Taupymas', 'Transportas']
        )

        context['accounts'] = views_helpers.render_accounts(
            self.request, _account, **{'months_amount_end': _MonthsBalance.amount_end})
        context['savings'] = views_helpers.render_savings(
            self.request, _fund, _pension)
        context['balance'] = _MonthsBalance.balance
        context['balance_totals'] = _MonthsBalance.totals
        context['balance_avg'] = _MonthsBalance.average
        context['amount_start'] = _MonthsBalance.amount_start
        context['months_amount_end'] = _MonthsBalance.amount_end
        context['accounts_amount_end'] = _account.balance_end
        context['amount_balance'] = _MonthsBalance.amount_balance
        context['total_market'] = _fund.total_market
        context['avg_incomes'] = _MonthsBalance.avg_incomes
        context['avg_expenses'] = _MonthsBalance.avg_expenses
        context['expenses'] = _MonthsExpenseType.balance
        context['expense_types'] = _expense_types
        context['expenses_totals'] = _MonthsExpenseType.totals
        context['expenses_average'] = _MonthsExpenseType.average
        context['no_incomes'] = _NoIncomes.summary
        context['save_sum'] = _NoIncomes.save_sum

        # charts data
        context['pie'] = _MonthsExpenseType.chart_data
        context['e'] = _MonthsBalance.expense_data
        context['i'] = _MonthsBalance.income_data
        context['s'] = _MonthsBalance.save_data

        return context


class SavingsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = SavingType
    model = SavingWorth
    form_class = SavingWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        _fund, _pension = views_helpers.saving_stats(
            self.request.user.profile.year)

        context['fund'] = _fund.balance
        context['fund_totals'] = _fund.totals
        context['pension'] = _pension.balance
        context['pension_totals'] = _pension.totals

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.profile.year

        _account = views_helpers.account_stats(year)

        context['accounts'] = _account.balance
        context['totals'] = _account.totals

        return context


class Month(IndexMixin):
    template_name = 'bookkeeping/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year
        month = self.request.user.profile.month

        _MonthExpenseType = MonthExpenseType(
            year,
            month,
            Expense.objects.day_expense_type(year, month),
            **{'Taupymas': Saving.objects.day_saving(year, month)}
        )
        _CalcDaySum = CalcDaySum(year)

        fact_incomes = Income.objects.income_sum(year, month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_expenses = _MonthExpenseType.total

        plan_incomes = get_value_from_dict(_CalcDaySum.incomes, month)
        plan_day_sum = get_value_from_dict(_CalcDaySum.day_input, month)
        plan_free_sum = get_value_from_dict(_CalcDaySum.expenses_free, month)
        plan_remains = get_value_from_dict(_CalcDaySum.remains, month)

        _DaySpending = DaySpending(
            year=year,
            month=month,
            month_df=_MonthExpenseType.balance_df,
            necessary=views_helpers.necessary_expense_types('Taupymas'),
            plan_day_sum=plan_day_sum,
            plan_free_sum=plan_free_sum,
            exceptions=Expense.objects.month_exceptions(year, month)
        )

        context['month_list'] = year_month_list(year)
        context['expenses'] = _MonthExpenseType.balance
        context['totals'] = _MonthExpenseType.totals
        context['expense_types'] = views_helpers.expense_types('Taupymas')
        context['day'] = current_day(year, month)
        context['spending_table'] = _DaySpending.spending

        context['plan_per_day'] = plan_day_sum
        context['plan_incomes'] = plan_incomes
        context['plan_remains'] = plan_remains
        context['fact_per_day'] = _DaySpending.avg_per_day
        context['fact_incomes'] = fact_incomes
        context['fact_remains'] = fact_incomes - fact_expenses

        return context
