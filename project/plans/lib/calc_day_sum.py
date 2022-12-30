from collections import namedtuple
from dataclasses import dataclass, field
from typing import Union

import pandas as pd
from django.db.models import F
from django.utils.translation import gettext as _

from ...core.lib.date import monthlen, monthname, monthnames
from ..models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                      SavingPlan)


@dataclass
class PlanCollectData:
    year: int = 1970
    month: int = 0

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

        self._df = self._calc_df()

        # filter data for current month
        if self._data.month:
            month = monthname(data.month)  # convert int to month name
            self._df = self._df.loc[:, month]

    @property
    def incomes(self) -> dict[str, float]:
        data = self._df.loc['incomes']
        return self._return_data(data)

    @property
    def savings(self) -> dict[str, float]:
        data = self._df.loc['savings']
        return self._return_data(data)

    @property
    def expenses_free(self) -> dict[str, float]:
        data = self._df.loc['expenses_free']
        return self._return_data(data)

    @property
    def expenses_necessary(self) -> dict[str, float]:
        data = self._df.loc['expenses_necessary']
        return self._return_data(data)

    @property
    def day_calced(self) -> dict[str, float]:
        data = self._df.loc['day_calced']
        return self._return_data(data)

    @property
    def day_input(self) -> dict[str, float]:
        data = self._df.loc['day_input']
        return self._return_data(data)

    @property
    def remains(self) -> dict[str, float]:
        data = self._df.loc['remains']
        return self._return_data(data)

    @property
    def necessary(self) -> dict[str, float]:
        data = self._df.loc['necessary']
        return self._return_data(data)

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

    @property
    def targets(self) -> dict[str, float]:
        if not self._data.month:
            return

        rtn = {}
        month = monthname(self._data.month)
        arr = self._data.expenses

        for item in arr:
            val = item.get(month, 0.0) or 0.0
            rtn[item.get('title', 'unknown')] = float(val)

        return rtn

    def _return_data(self, data: Union[pd.Series, float]) -> Union[dict, float]:
        ''' If data is pandas Serries convert data to dictionary '''

        return data.to_dict() if isinstance(data, pd.Series) else data

    def _sum(self, arr: list):
        df = pd.DataFrame(arr)

        if df.empty:
            return

        # convert to_numeric decimal values
        df = df.apply(pd.to_numeric, errors='ignore')

        df.loc['sum', :] = df.sum(axis=0)
        return df.loc['sum', :]

    def _create_df(self) -> pd.DataFrame:
        df = pd.DataFrame(columns=monthnames(), dtype=float)
        # create rows with all values 0
        row_names = ['incomes', 'savings', 'necessary',
                     'expenses_necessary', 'expenses_free',
                     'day_calced', 'day_input', 'remains',]
        for name in row_names:
            df.loc[name, :] = 0.0
        #
        df.loc['month_lenght', :] = df.apply(
            lambda x: monthlen(self._year, x.name), axis=0)

        return df

    def _calc_df(self) -> None:
        df = self._create_df()

        df.loc['incomes', :] = self._sum(self._data.incomes)
        df.loc['savings', :] = self._sum(self._data.savings)
        df.loc['day_input', :] = self._sum(self._data.days)
        df.loc['necessary', :] = self._sum(self._data.necessary)

        filtered = [d for d in self._data.expenses if d['necessary']]
        df.loc['expenses_necessary', :] = self._sum(filtered)
        filtered = [d for d in self._data.expenses if not d['necessary']]
        df.loc['expenses_free', :] = self._sum(filtered)

        df.loc['expenses_necessary'] = \
            0 \
            + df.loc['expenses_necessary'] \
            + df.loc['savings'] \
            + df.loc['necessary'] \

        df.loc['expenses_free'] = \
            0 \
            + df.loc['incomes'] \
            - df.loc['expenses_necessary'] \

        df.loc['day_calced'] = \
            0 \
            + (df.loc['expenses_free'] / df.loc['month_lenght'])

        df.loc['remains'] = \
            0 \
            + df.loc['expenses_free'] \
            - (df.loc['day_input'] * df.loc['month_lenght'])

        # fill cell with NaN
        return df.fillna(0.0)
