import pandas as pd

from .filter_frame import FilterDf
from .stats_utils import CalcBalance


class StatsSavings(object):
    def __init__(self, year, data):
        self._year = year
        self._balance = pd.DataFrame()

        # if there are no saving_types
        if data.get('savingtype') is None or data['savingtype'].empty:
            return

        self._balance = data['savingtype']
        self._data = FilterDf(year, data)

        self._prepare_balance()
        self._calc_balance()

    @property
    def balance(self):
        return (
            self._balance.to_dict('index') if not self._balance.empty
            else self._balance
        )

    def _prepare_balance(self):
        self._balance.set_index(['title'], inplace=True)

        self._balance.loc[:, 'past_amount'] = 0.00
        self._balance.loc[:, 'past_fee'] = 0.00
        self._balance.loc[:, 'incomes'] = 0.00
        self._balance.loc[:, 'fees'] = 0.00
        self._balance.loc[:, 'invested'] = 0.00

    def _calc_balance(self):
        cb = CalcBalance('saving_type', self._balance)

        cb.calc(self._data.savings, '+', 'incomes')
        cb.calc(self._data.savings, '+', 'fees', 'fee')

        cb.calc(self._data.savings_past, '+', 'past_amount')
        cb.calc(self._data.savings_past, '+', 'past_fee', 'fee')

        cb.calc(self._data.savings_change_to_past, '+', 'past_amount')
        cb.calc(self._data.savings_change_to_past, '+', 'past_fee', 'fee')

        cb.calc(self._data.savings_change_from_past, '-', 'past_amount')
        cb.calc(self._data.savings_change_from_past, '+', 'past_fee', 'fee')

        cb.calc(self._data.savings_change_to, '+', 'incomes')
        cb.calc(self._data.savings_change_to, '+', 'fees', 'fee')

        cb.calc(self._data.savings_change_from, '-', 'incomes')
        cb.calc(self._data.savings_change_from, '+', 'fees', 'fee')

        cb.calc(self._data.savings_close_from, '-', 'incomes')

        cb.calc(self._data.savings_close_from_past, '-', 'past_amount')


        self._balance.incomes = self._balance.incomes + self._balance.past_amount
        self._balance.fees = self._balance.fees + self._balance.past_fee

        self._balance.invested = self._balance.incomes - self._balance.fees
