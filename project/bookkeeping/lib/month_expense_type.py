from datetime import datetime
from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin


class MonthExpenseType(CalcBalanceMixin):
    def __init__(self, year: int, month: int, expenses: List[Dict]):
        self._year = year if year else datetime.now().year
        self._month = month if month else datetime.now().month
        self._balance = self._create_df()

        if not expenses:
            return

        self._calc(expenses)

    @property
    def balance(self) -> List[Dict[str, float]]:
        return super().balance(self._balance)

    @property
    def totals(self) -> Dict[str, float]:
        return super().totals(self._balance)

    @property
    def average(self) -> Dict[str, float]:
        return super().average(self._balance)

    def _create_df(self) -> pd.DataFrame():
        df = pd.DataFrame({
            'date': pd.date_range(
                start=pd.Timestamp(self._year, self._month, 1),
                end=pd.Timestamp(self._year, self._month, 1) + pd.offsets.MonthEnd(0),
                freq='D'
            )
        })
        df.loc[:, 'total'] = 0.0
        df.set_index('date', inplace=True)

        return df

    def _calc(self, expenses: List[Dict]) -> None:
        # copy values from expenses to data_frame
        for _dict in expenses:
            self._balance.at[_dict['date'], _dict['title']] = _dict['sum']

        self._balance.fillna(0.0, inplace=True)

        # convert to float and datetime.date
        for col in self._balance.columns:
            self._balance[col] = pd.to_numeric(self._balance[col])

        self._balance.loc[:, 'total'] = self._balance.sum(axis=1)
