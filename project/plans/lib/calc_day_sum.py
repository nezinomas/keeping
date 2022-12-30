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

        self._calc_df()

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

    def _sum(self, arr: list, row_name: str, necessary: int = -1):
        df = pd.DataFrame(arr)

        if df.empty:
            return

        # convert to_numeric january-december columns decimal values
        df = df.apply(pd.to_numeric, errors='ignore')

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

        self._df.loc['expenses_necessary'] = \
            0 \
            + self._df.loc['expenses_necessary'] \
            + self._df.loc['savings'] \
            + self._df.loc['necessary'] \

        self._df.loc['expenses_free'] = \
            0 \
            + self._df.loc['incomes'] \
            - self._df.loc['expenses_necessary'] \

        self._df.loc['day_calced'] = \
            0 \
            + (self._df.loc['expenses_free'] / self._df.loc['m'])

        self._df.loc['remains'] = \
            0 \
            + self._df.loc['expenses_free'] \
            - (self._df.loc['day_input'] * self._df.loc['m'])

        # fill cell with NaN
        self._df.fillna(0.0, inplace=True)
