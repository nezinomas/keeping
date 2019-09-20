from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin


class MonthsExpenseType(CalcBalanceMixin):
    def __init__(self, expenses: List[Dict]):
        self._balance = pd.DataFrame()

        if not expenses:
            return

        self._calc(expenses)

    @property
    def balance(self) -> List[Dict[str, float]]:
        val = None
        balance = self._balance.copy()

        if not balance.empty:
            val = balance.to_dict('records')

        return val

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

    def _calc(self, expenses: List[Dict[str, float]]) -> None:
        year = expenses[0]['date'].year

        # create empty DataFrame object with index containing all months
        date_range = pd.date_range(f'{year}', periods=12, freq='MS')
        df = pd.DataFrame(date_range, columns=['date'])
        df.set_index('date', inplace=True)

        # copy values from expenses to data_frame
        for _dict in expenses:
            df.at[_dict['date'], _dict['title']] = _dict['sum']

        df.fillna(0.0, inplace=True)
        df.reset_index(inplace=True)

        # convert to float and datetime.date
        for col in df.columns:
            if col == 'date':
                df[col] = df[col].dt.date
            else:
                df[col] = pd.to_numeric(df[col])

        df.loc[:, 'total'] = df.sum(axis=1)

        self._balance = df
