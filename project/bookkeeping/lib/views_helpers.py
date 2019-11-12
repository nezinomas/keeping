from collections import Counter, defaultdict
from typing import Dict, List

from django.template.loader import render_to_string

from ...accounts.models import AccountBalance
from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict as get_val
from ...core.lib.utils import sum_all, sum_col
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...pensions.models import PensionBalance
from ...plans.lib.calc_day_sum import CalcDaySum
from ...savings.models import Saving, SavingBalance
from ...transactions.models import SavingClose
from ..lib.day_spending import DaySpending
from ..lib.expense_summary import DayExpense, MonthExpense
from ..lib.no_incomes import NoIncomes
from ..lib.year_balance import YearBalance


def expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType.objects.items()
        .values_list('title', flat=True)
    )

    [qs.append(x) for x in args]

    qs.sort()

    return qs


def necessary_expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType.objects.items()
        .filter(necessary=True)
        .values_list('title', flat=True)
    )

    [qs.append(x) for x in args]

    qs.sort()

    return qs


def split_funds(lst: List[Dict], key: str) -> List[Dict]:
    return list(filter(lambda x: key in x['title'].lower(), lst))


def sum_detailed(dataset, group_by_key, sum_value_keys):
    container = defaultdict(Counter)

    for item in dataset:
        key = item[group_by_key]
        values = {k: item[k] for k in sum_value_keys}
        container[key].update(values)

    new_dataset = []
    for item in container.items():
        new_dataset.append({group_by_key: item[0], **item[1]})

    new_dataset.sort(key=lambda item: item[group_by_key])

    return new_dataset


def percentage_from_incomes(incomes, savings):
    if incomes and savings:
        return (savings * 100) / incomes


def render_savings(request, fund, **kwargs):
    return render_to_string(
        'bookkeeping/includes/savings_worth_list.html',
        {
            'fund': fund, 'fund_total_row': sum_all(fund),
            **kwargs
        },
        request
    )


def render_pensions(request, pension, **kwargs):
    return render_to_string(
        'bookkeeping/includes/pensions_worth_list.html',
        {
            'pension': pension, 'pension_total_row': sum_all(pension),
            **kwargs
        },
        request
    )


def render_no_incomes(request,
                      money: float,
                      avg_expenses: float,
                      avg_type_expenses: Dict[str, float],
                      funds: List[Dict]):
    _NoIncomes = NoIncomes(
        money=money,
        fund=sum_col(split_funds(funds, 'lx'), 'market_value'),
        pension=sum_col(split_funds(funds, 'invl'), 'market_value'),
        avg_expenses=avg_expenses,
        avg_type_expenses=avg_type_expenses,
        not_use=[
            'Darbas',
            'Laisvalaikis',
            'Paskolos',
            'Taupymas',
            'Transportas',
        ]
    )
    context = {
        'no_incomes': _NoIncomes.summary,
        'save_sum': _NoIncomes.save_sum,
    }

    return render_to_string(
        'bookkeeping/includes/no_incomes.html',
        context,
        request
    )


class MonthHelper():
    def __init__(self, request, year, month):
        self.request = request
        self.year = year
        self.month = month

        qs_expenses = Expense.objects.day_expense_type(year, month)
        qs_savings = Saving.objects.day_saving(year, month)

        self._day = DayExpense(
            year=year,
            month=month,
            expenses=qs_expenses,
            **{'Taupymas': qs_savings}
        )

        self._day_plans = CalcDaySum(year)

        self._spending = DaySpending(
            year=year,
            month=month,
            month_df=self._day.expenses,
            exceptions=self._day.exceptions,
            necessary=necessary_expense_types('Taupymas'),
            plan_day_sum=get_val(self._day_plans.day_input, month),
            plan_free_sum=get_val(self._day_plans.expenses_free, month),
        )

        self.expenses_types = expense_types('Taupymas')
        self.current_day = current_day(year, month)

    def render_chart_targets(self):
        targets = self._day_plans.targets(self.month, 'Taupymas')
        (categories, data_target, data_fact) = self._day.chart_targets(
            self.expenses_types, targets)

        context = {
            'chart_targets_categories': categories,
            'chart_targets_data_target': data_target,
            'chart_targets_data_fact': data_fact,
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_targets.html',
            context=context,
            request=self.request
        )

    def render_chart_expenses(self):
        context = {
            'expenses': self._day.chart_expenses(self.expenses_types)
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_expenses.html',
            context=context,
            request=self.request
        )

    def render_spending(self):
        context = {
            'spending_table': self._spending.spending,
            'day': self.current_day,
        }

        return render_to_string(
            template_name='bookkeeping/includes/spending.html',
            context=context,
            request=self.request
        )

    def render_info(self):
        fact_incomes = Income.objects.income_sum(self.year, self.month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_expenses = self._day.total

        plan_incomes = get_val(self._day_plans.incomes, self.month)
        plan_day_sum = get_val(self._day_plans.day_input, self.month)
        plan_free_sum = get_val(self._day_plans.expenses_free, self.month)
        plan_remains = get_val(self._day_plans.remains, self.month)

        context = {
            'plan_per_day': plan_day_sum,
            'plan_incomes': plan_incomes,
            'plan_remains': plan_remains,
            'fact_per_day': self._spending.avg_per_day,
            'fact_incomes': fact_incomes,
            'fact_remains': fact_incomes - fact_expenses,
        }

        return render_to_string(
            template_name='bookkeeping/includes/spending_info.html',
            context=context,
            request=self.request
        )

    def render_month_table(self):
        context = {
            'expenses': self._day.balance,
            'total_row': self._day.total_row,
            'expense_types': self.expenses_types,
            'day': self.current_day,
        }

        return render_to_string(
            template_name='bookkeeping/includes/month_table.html',
            context=context,
            request=self.request
        )


class IndexHelper():
    def __init__(self, request, year):
        self.request = request
        self.year = year

        self._account = [*AccountBalance.objects.items(year)]
        self._fund = [*SavingBalance.objects.items(year)]
        self._pension = [*PensionBalance.objects.items(year)]
        self._expense_types = expense_types('Taupymas')

        qs_income = Income.objects.income_sum(year)
        qs_savings = Saving.objects.month_saving(year)
        qs_savings_close = SavingClose.objects.month_sum(year)
        qs_ExpenseType = Expense.objects.month_expense_type(year)

        self._MonthExpense = MonthExpense(
            year, qs_ExpenseType, **{'Taupymas': qs_savings})

        self._YearBalance = YearBalance(
            year=year,
            incomes=qs_income,
            expenses=self._MonthExpense.total_column,
            savings_close=qs_savings_close,
            amount_start=sum_col(self._account, 'past'))

        wealth_money = self._YearBalance.amount_end + sum_col(self._fund, 'market_value')
        wealth = wealth_money + sum_col(self._pension, 'market_value')

    def render_accounts(self):
        context = {
            'accounts': self._account,
            'total_row': sum_all(self._account),
            'accounts_amount_end': sum_col(self._account, 'balance'),
            'months_amount_end': self._YearBalance.amount_end,
        }
        return render_to_string(
            'bookkeeping/includes/accounts_worth_list.html',
            context,
            self.request
        )

    def render_no_incomes(self):
        fund = split_funds(self._fund, 'lx')
        pension = split_funds(self._fund, 'invl')

        obj = NoIncomes(
            money=self._YearBalance.amount_end,
            fund=sum_col(fund, 'market_value'),
            pension=sum_col(pension, 'market_value'),
            avg_expenses=self._YearBalance.avg_expenses,
            avg_type_expenses=self._MonthExpense.average,
            not_use=[
                'Darbas',
                'Laisvalaikis',
                'Paskolos',
                'Taupymas',
                'Transportas',
            ]
        )
        context = {
            'no_incomes': obj.summary,
            'save_sum': obj.save_sum,
        }

        return render_to_string(
            'bookkeeping/includes/no_incomes.html',
            context,
            self.request
        )
