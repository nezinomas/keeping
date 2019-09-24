from datetime import datetime
from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import (BalanceStats, df_days_of_month,
                                   df_months_of_year)


class MonthExpenseType(BalanceStats):
    def __init__(self, year: int, month: int, expenses: List[Dict]):
        self._balance = df_days_of_month(year, month)

        if not expenses:
            return

        self._calc(expenses)

    def _calc(self, expenses: List[Dict]) -> None:
        # copy values from expenses to data_frame
        for _dict in expenses:
            self._balance.at[_dict['date'], _dict['title']] = float(_dict['sum'])

        self._balance.fillna(0.0, inplace=True)

        self._balance['total'] = self._balance.sum(axis=1)
