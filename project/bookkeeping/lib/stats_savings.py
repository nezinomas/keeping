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

        if not isinstance(_df, pd.DataFrame):
            return

        if _df.empty:
            return

        _df.set_index('saving_type', inplace=True)

        _idx = _df.index.tolist()

        # copy market values from savings_worth to _balance
        for i in _idx:
            self._balance.at[i, 'market_value'] = _df.at[i, 'price']

        # calculate percent of profit/loss
        self._balance['profit_incomes_proc'] = (
            self._balance[['market_value', 'incomes']]
            .apply(self._calc_percent, axis=1)
        )

        self._balance['profit_invested_proc'] = (
            self._balance[['market_value', 'invested']]
            .apply(self._calc_percent, axis=1)
        )

        # calculate sum of profit/loss
        self._balance['profit_incomes_sum'] = (
            self._balance[['market_value', 'incomes']]
            .apply(self._calc_sum, axis=1)
        )

        self._balance['profit_invested_sum'] = (
            self._balance[['market_value', 'invested']]
            .apply(self._calc_sum, axis=1)
        )

    def _calc_percent(self, args):
        market = args[0]
        invested = args[1]

        if market != 0.0:
            return (market*100/invested)-100
        else:
            return 0.0

    def _calc_sum(self, args):
        market = args[0]
        invested = args[1]

        if market != 0.0:
            return market - invested
        else:
            return 0.0
