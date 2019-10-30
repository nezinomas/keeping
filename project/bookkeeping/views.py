from ..accounts.models import Account, AccountBalance
from ..core.lib.date import current_day, year_month_list
from ..core.lib.utils import get_value_from_dict, sum_all, sum_col
from ..core.mixins.formset import FormsetMixin
from ..core.mixins.views import CreateAjaxMixin, IndexMixin
from ..expenses.models import Expense
from ..incomes.models import Income
from ..plans.lib.calc_day_sum import CalcDaySum
from ..plans.models import DayPlan
from ..savings.models import Saving, SavingType
from ..transactions.models import SavingClose
from .forms import AccountWorthForm, SavingWorthForm
from .lib import views_helpers
from .lib.day_spending import DaySpending
from .lib.expense_stats import MonthExpenseType, MonthsExpenseType
from .lib.months_balance import MonthsBalance
from .lib.no_incomes import NoIncomes
from .lib.summary import collect_summary_data
from .models import AccountWorth, SavingWorth


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = self.request.user.profile.year

        _account = [*AccountBalance.objects.items(year)]

        _fund, _pension = views_helpers.split_savings_stats(year)
        _expense_types = views_helpers.expense_types('Taupymas')

        qs_income = Income.objects.income_sum(year)
        qs_savings = Saving.objects.month_saving(year)
        qs_savings_close = SavingClose.objects.month_sum(year)
        qs_ExpenseType = Expense.objects.month_expense_type(year)

        _MonthsExpenseType = MonthsExpenseType(
            year, qs_ExpenseType, **{'Taupymas': qs_savings})

        _MonthsBalance = MonthsBalance(
            year=year,
            incomes=qs_income,
            expenses=_MonthsExpenseType.total_column,
            savings_close=qs_savings_close,
            amount_start=sum_col(_account, 'past'))

        total_market = sum_col(_fund, 'market_value')
        _NoIncomes = NoIncomes(
            money=_MonthsBalance.amount_end,
            fund=total_market,
            pension=total_market,
            avg_expenses=_MonthsBalance.avg_expenses,
            avg_type_expenses=_MonthsExpenseType.average,
            not_use=[
                'Darbas',
                'Laisvalaikis',
                'Paskolos',
                'Taupymas',
                'Transportas']
        )

        context['year'] = year
        context['accounts'] = views_helpers.render_accounts(
            self.request, _account,
            **{'months_amount_end': _MonthsBalance.amount_end})
        context['savings'] = views_helpers.render_savings(
            self.request, _fund, _pension)
        context['balance'] = _MonthsBalance.balance
        context['balance_total_row'] = _MonthsBalance.total_row
        context['balance_avg'] = _MonthsBalance.average
        context['amount_start'] = _MonthsBalance.amount_start
        context['months_amount_end'] = _MonthsBalance.amount_end
        context['accounts_amount_end'] = sum_col(_account, 'balance')
        context['amount_balance'] = _MonthsBalance.amount_balance
        context['total_market'] = total_market
        context['avg_incomes'] = _MonthsBalance.avg_incomes
        context['avg_expenses'] = _MonthsBalance.avg_expenses
        context['expenses'] = _MonthsExpenseType.balance
        context['expense_types'] = _expense_types
        context['expenses_total_row'] = _MonthsExpenseType.total_row
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
        year = self.request.user.profile.year

        _fund, _pension = views_helpers.split_savings_stats(year)

        context['fund'] = _fund
        context['fund_total_row'] = sum_all(_fund)
        context['pension'] = _pension
        context['pension_total_row'] = sum_all(_pension)

        return context


class AccountsWorthNew(FormsetMixin, CreateAjaxMixin):
    type_model = Account
    model = AccountWorth
    form_class = AccountWorthForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.user.profile.year

        qsa = Account.objects.items().values('id', 'title')
        typesa = {x['title']: x['id'] for x in qsa}
        acc = collect_summary_data(year, typesa, 'accounts')

        _account = AccountBalance.objects.items()

        context['accounts'] = _account
        context['total_row'] = sum_all(_account)

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

        expenses_types = views_helpers.expense_types('Taupymas')

        targets = _CalcDaySum.targets(month, 'Taupymas')
        (categories, data_target, data_fact) = _MonthExpenseType.chart_targets(
            expenses_types, targets)

        _DaySpending = DaySpending(
            year=year,
            month=month,
            month_df=_MonthExpenseType.expenses,
            necessary=views_helpers.necessary_expense_types('Taupymas'),
            plan_day_sum=plan_day_sum,
            plan_free_sum=plan_free_sum,
            exceptions=_MonthExpenseType.exceptions
        )

        context['month_list'] = year_month_list(year)
        context['expenses'] = _MonthExpenseType.balance
        context['total_row'] = _MonthExpenseType.total_row
        context['expense_types'] = expenses_types
        context['day'] = current_day(year, month)
        context['spending_table'] = _DaySpending.spending

        context['plan_per_day'] = plan_day_sum
        context['plan_incomes'] = plan_incomes
        context['plan_remains'] = plan_remains
        context['fact_per_day'] = _DaySpending.avg_per_day
        context['fact_incomes'] = fact_incomes
        context['fact_remains'] = fact_incomes - fact_expenses

        context['chart_expenses'] = _MonthExpenseType.chart_expenses(
            expenses_types)
        context['chart_targets_categories'] = categories
        context['chart_targets_data_target'] = data_target
        context['chart_targets_data_fact'] = data_fact

        return context
