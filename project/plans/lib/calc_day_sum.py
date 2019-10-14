import calendar
from collections import namedtuple
from decimal import Decimal
from typing import Dict, List

import pandas as pd
from django.db.models import F

from ...core.lib.date import monthlen, monthname, monthnames
from ..models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                      SavingPlan)


class CollectData:
    _incomes: List[Dict[str, Decimal]] = []
    _expenses: List[Dict[str, Decimal]] = []
    _savings: List[Dict[str, Decimal]] = []
    _days: List[Dict[str, Decimal]] = []
    _necessary: List[Dict[str, Decimal]] = []

    def __init__(self, year: int = 1970):
        self._year = year

        self._incomes = (
            IncomePlan.objects.year(self._year)
            .values(*monthnames()))

        self._expenses = (
            ExpensePlan.objects.year(self._year)
            .values(
                *monthnames(),
                necessary=F('expense_type__necessary'),
                title=F('expense_type__title')
            ))

        self._savings = (
            SavingPlan.objects.year(self._year)
            .values(*monthnames()))

        self._days = (
            DayPlan.objects.year(self._year)
            .values(*monthnames()))

        self._necessary = (
            NecessaryPlan.objects.year(self._year)
            .values(*monthnames()))

    @property
    def incomes(self) -> List[Dict[str, Decimal]]:
        return self._incomes

    @property
    def expenses(self) -> List[Dict[str, Decimal]]:
        return self._expenses

    @property
    def savings(self) -> List[Dict[str, Decimal]]:
        return self._savings

    @property
    def days(self) -> List[Dict[str, Decimal]]:
        return self._days

    @property
    def necessary(self) -> List[Dict[str, Decimal]]:
        return self._necessary


class CalcDaySum():
    def __init__(self, year: int):
        self._year = year
        self._data = self._get_data()

        self._calc_df()

    @property
    def incomes(self) -> Dict[str, float]:
        return self._df.loc['incomes'].to_dict()

    @property
    def savings(self) -> Dict[str, float]:
        return self._df.loc['savings'].to_dict()

    @property
    def expenses_free(self) -> Dict[str, float]:
        return self._df.loc['expenses_free'].to_dict()

    @property
    def expenses_necessary(self) -> Dict[str, float]:
        return self._df.loc['expenses_necessary'].to_dict()

    @property
    def day_calced(self) -> Dict[str, float]:
        return self._df.loc['day_calced'].to_dict()

    @property
    def day_input(self) -> Dict[str, float]:
        return self._df.loc['day_input'].to_dict()

    @property
    def remains(self) -> Dict[str, float]:
        return self._df.loc['remains'].to_dict()

    @property
    def necessary(self) -> Dict[str, float]:
        return self._df.loc['necessary'].to_dict()

    @property
    def plans_stats(self):
        dicts = [
            dict({'type': 'Būtinos išlaidos'}, **self.expenses_necessary),
            dict({'type': 'Lieka kasdienybei', **self.expenses_free}),
            dict({'type': 'Suma dienai, max galima'}, **self.day_calced),
            dict({'type': 'Likutis'}, **self.remains),
        ]

        # list of dictionaries convert to list of objects
        return [namedtuple("Items", item.keys())(*item.values()) for item in dicts]

    def targets(self,
                month: int,
                saving_title: str=None) -> Dict[str, float]:
        rtn = {}

        month = monthname(month)
        arr = self._data._expenses

        for lst in arr:
            val = lst.get(month, 0.0)
            val = val if val else 0.0
            rtn[lst.get('title', 'unknown')] = float(val)

        if saving_title:
            savings = self.savings
            rtn[saving_title] = float(savings.get(month, 0.0))

        return rtn

    def _get_data(self):
        return CollectData(self._year)

    def _sum(self, arr: List, row_name: str, necessary: int = -1):
        df = pd.DataFrame(arr, dtype=float)

        if df.empty:
            return

        if necessary >= 0:
            # filter expensy_type by necessary/ordinary
            df = df.loc[df['necessary'] == necessary]

        df.loc['sum', :] = df.sum(axis=0)

        self._df.loc[row_name, :] = df.loc['sum', :]

    def _create_df(self) -> pd.DataFrame:
        df = pd.DataFrame(columns=monthnames(), dtype=float)

        df.loc['incomes', :] = 0.0
        df.loc['savings', :] = 0.0
        df.loc['necessary', :] = 0.0
        df.loc['expenses_necessary', :] = 0.0
        df.loc['expenses_free', :] = 0.0
        df.loc['day_calced', :] = 0.0
        df.loc['day_input', :] = 0.0
        df.loc['remains', :] = 0.0

        df.loc['m', :] = df.apply(
            lambda x: monthlen(self._year, x.name), axis=0)

        return df

    def _calc_df(self) -> None:
        self._df = self._create_df()

        self._sum(self._data.incomes, 'incomes')
        self._sum(self._data.savings, 'savings')
        self._sum(self._data.days, 'day_input')
        self._sum(self._data.necessary, 'necessary')
        self._sum(self._data.expenses, 'expenses_necessary', 1)
        self._sum(self._data.expenses, 'expenses_free', 0)

        self._df.loc['expenses_necessary'] = (
            0
            + self._df.loc['expenses_necessary']
            + self._df.loc['savings']
            + self._df.loc['necessary']
        )
        self._df.loc['expenses_free'] = (
            self._df.loc['incomes'] - self._df.loc['expenses_necessary']
        )
        self._df.loc['day_calced'] = (
            self._df.loc['expenses_free'] / self._df.loc['m']
        )
        self._df.loc['remains'] = (
            self._df.loc['expenses_free'] - self._df.loc['day_input'] * self._df.loc['m']
        )

        # fill cell with NaN
        self._df.fillna(0.0, inplace=True)
