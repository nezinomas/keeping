from datetime import datetime
from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin, BalanceStats


class MonthExpenseType(BalanceStats, CalcBalanceMixin):
    def __init__(self, year: int, month: int, expenses: List[Dict]):
        self._balance = super().df_days_of_month(year, month)

        if not expenses:
            return

        self._calc(expenses)

    def _calc(self, expenses: List[Dict]) -> None:
        # copy values from expenses to data_frame
        for _dict in expenses:
            self._balance.at[_dict['date'], _dict['title']] = _dict['sum']

        self._balance.fillna(0.0, inplace=True)

        # convert to float and datetime.date
        for col in self._balance.columns:
            self._balance[col] = pd.to_numeric(self._balance[col])

        self._balance['total'] = self._balance.sum(axis=1)
