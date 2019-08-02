import pandas as pd

from ...core.tests.utils import _print

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
        self._calc_worth()

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
        self._balance.loc[:, 'market_value'] = 0.00
        self._balance.loc[:, 'profit_incomes_proc'] = 0.00
        self._balance.loc[:, 'profit_incomes_sum'] = 0.00
        self._balance.loc[:, 'profit_invested_proc'] = 0.00
        self._balance.loc[:, 'profit_invested_sum'] = 0.00

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

    def _calc_worth(self):
        _df = self._data.savings_worth

        try:
            _df.set_index('saving_type', inplace=True)
        except:
            return

        _idx = _df.index.tolist()

        for i in _idx:
            self._balance.at[i, 'market_value'] = _df.at[i, 'price']

        self._balance.profit_incomes_proc = (
            self._balance.market_value*100/self._balance.incomes)-100
        self._balance.profit_invested_proc = (
            self._balance.market_value*100/self._balance.invested)-100

        self._balance.profit_incomes_sum = (
            self._balance.market_value - self._balance.incomes)
        self._balance.profit_invested_sum = (
            self._balance.market_value - self._balance.invested)
