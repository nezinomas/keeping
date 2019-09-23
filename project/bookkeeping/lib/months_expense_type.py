from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin


class MonthsExpenseType(CalcBalanceMixin):
    def __init__(self, year, expenses: List[Dict]):
        self._year = year
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

    @property
    def chart_data(self) -> List[Dict[str, float]]:
        rtn = []
        arr = super().totals(self._balance)

        if arr:
            # delete total cell
            del arr['total']

            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transfort arr for pie chart
            rtn = [{'name': key, 'y': value} for key, value in arr.items()]
        return rtn

    def _create_df(self) -> pd.DataFrame:
        # create empty DataFrame object with index containing all months
        date_range = pd.date_range(f'{self._year}', periods=12, freq='MS')
        df = pd.DataFrame(date_range, columns=['date'])

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

        self._balance['total'] = self._balance.sum(axis=1)
