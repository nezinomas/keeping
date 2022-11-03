from collections import namedtuple
from decimal import Decimal
from typing import Dict, List

import pandas as pd
from django.db.models import F
from django.utils.translation import gettext as _

from ...core.lib.date import monthlen, monthname, monthnames
from ..models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                      SavingPlan)
from dataclasses import dataclass, field


@dataclass
class PlanCollectData:
    year: int = 1970

    incomes: list[dict] = \
        field(init=False, default_factory=list)
    expenses: list[dict] = \
        field(init=False, default_factory=list)
    savings: list[dict] = \
        field(init=False, default_factory=list)
    days: list[dict] = \
        field(init=False, default_factory=list)
    necessary: list[dict] = \
        field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = \
            IncomePlan.objects \
            .year(self.year) \
            .values(*monthnames())

        self.expenses = \
            ExpensePlan.objects \
            .year(self.year) \
            .values(
                *monthnames(),
                necessary=F('expense_type__necessary'),
                title=F('expense_type__title'))

        self.savings = \
            SavingPlan.objects \
            .year(self.year) \
            .values(*monthnames())

        self.days = \
            DayPlan.objects \
            .year(self.year) \
            .values(*monthnames())

        self.necessary = \
            NecessaryPlan.objects \
            .year(self.year) \
            .values(*monthnames())


class PlanCalculateDaySum():
    def __init__(self, data: PlanCollectData):
        self._data = data
        self._year = data.year

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
            dict({'type': _('Necessary expenses')}, **self.expenses_necessary),
            dict({'type': _('Remains for everyday'), **self.expenses_free}),
            dict({'type': _('Sum per day, max possible')}, **self.day_calced),
            dict({'type': _('Residual')}, **self.remains),
        ]

        # list of dictionaries convert to list of objects
        return [namedtuple("Items", item.keys())(*item.values()) for item in dicts]

    def targets(self, month: int) -> Dict[str, float]:
        rtn = {}

        month = monthname(month)
        arr = self._data.expenses
        print(f'{arr=}')
        for item in arr:
            val = item.get(month, 0.0) or 0.0
            rtn[item.get('title', 'unknown')] = float(val)

        return rtn

    def _sum(self, arr: List, row_name: str, necessary: int = -1):
        df = pd.DataFrame(arr)

        if df.empty:
            return

        # drop non numeric columns
        _drop = ['necessary', 'title']
        _cols = df.columns
        for x in _drop:
            if x in _cols:
                _cols.drop(x)

        # convert to_numeric january-december columns decimal values
        df[_cols] = df[_cols].apply(pd.to_numeric, errors='ignore')

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
