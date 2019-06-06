import calendar
from collections import namedtuple
from decimal import Decimal
from time import strptime

import pandas as pd
from django_pandas.io import read_frame

from ..models import ExpensePlan, ExpenseType, IncomePlan, SavingPlan


class DaySum(object):
    def __init__(self, year):
        self._year = year

        self._incomes = self._get_incomes().sum()
        self._savings = self._get_savings().sum()
        self._expenses = self._get_expenses()

        self._expenses_necessary = self._get_expenses_necessary()

        self._expenses_necessary_sum = self._calc_expenses_necessary_sum()
        self._expenses_free = self._calc_expenses_free()
        self._day_sum = self._calc_day_sum()

    @property
    def incomes(self):
        return self._incomes.to_dict()

    @property
    def savings(self):
        return self._savings.to_dict()

    @property
    def expenses_necessary(self):
        return self._expenses_necessary

    @property
    def expenses_necessary_sum(self):
        return self._expenses_necessary_sum.to_dict()

    @property
    def expenses_free(self):
        return self._expenses_free.to_dict()

    @property
    def day_sum(self):
        return self._day_sum

    @property
    def plans_stats(self):
        dicts = [
            dict({'type': 'Būtinos išlaidos'}, **self.expenses_necessary_sum),
            dict({'type': 'Lieka kasdienybei', **self.expenses_free}),
            dict({'type': 'Suma dienai'}, **self.day_sum),
        ]

        # list of dictionaries convert to list of objects
        return [namedtuple("Items", item.keys())(*item.values()) for item in dicts]

    def _get_incomes(self):
        qs = IncomePlan.objects.items(**{'year': self._year})
        df = read_frame(qs)

        df = df.reset_index(drop=True).set_index('income_type')

        return df

    def _get_savings(self):
        qs = SavingPlan.objects.items(**{'year': self._year})
        df = read_frame(qs)

        df = df.reset_index(drop=True).set_index('saving_type')

        return df

    def _get_expenses(self):
        qs = ExpensePlan.objects.items(**{'year': self._year})
        df = read_frame(qs)

        if df.empty:
            df.loc[len(df)] = 0

        df = df.reset_index(drop=True).set_index('expense_type')

        return df

    def _get_expenses_necessary(self):
        qs = ExpenseType.objects.filter(necessary=True).values_list('title', flat=True)

        return list(qs)

    def _calc_expenses_necessary_sum(self):
        try:
            df = self._expenses.loc[self._expenses_necessary, :]
        except:
            df = self._expenses

        df = df.sum()
        df = df.add(self._savings, fill_value=0)

        return df

    def _calc_expenses_free(self):
        df = self._incomes.sub(self._expenses_necessary_sum, axis='rows')

        return df

    def _calc_day_sum(self):
        df = self.expenses_free

        for column_name, column_value in df.items():
            month = self._month(column_name)

            if column_value and month:
                df[column_name] = column_value / month

        return df

    def _month(self, word):
        if word not in [x.lower() for x in calendar.month_name[1:]]:
            return None

        new = word[0].upper() + word[1:3].lower()
        num = strptime(new, '%b').tm_mon

        return calendar.monthrange(self._year, num)[1]
