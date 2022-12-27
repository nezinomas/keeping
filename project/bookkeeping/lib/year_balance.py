from datetime import datetime

from pandas import DataFrame as DF

from ..lib.make_dataframe import MakeDataFrame
from .balance_base import BalanceBase


class YearBalance(BalanceBase):
    def __init__(self,
                 data: MakeDataFrame,
                 amount_start: float = 0.0):

        '''
        data: MakeDataFrame object

        amount_start: year start worth amount

        awailable keys in data: incomes, expenses, savings, savings_close, borrow, borrow_return, lend, lend_return
        '''

        try:
            self._amount_start = float(amount_start)
        except TypeError:
            self._amount_start = 0.0

        self._year = data.year
        self._balance = self._calc_balance_and_money_flow(data.data)

        super().__init__(self._balance)

    @property
    def amount_start(self) -> float:
        return self._amount_start

    @property
    def amount_end(self) -> float:
        try:
            val = self._balance['money_flow'].values[-1]
        except (KeyError, IndexError):
            val = 0.0

        return val

    @property
    def amount_balance(self) -> float:
        t = super().total_row

        return t.get('balance', 0.0)

    @property
    def avg_incomes(self) -> float:
        avg = super().average

        return avg.get('incomes', 0.0)

    @property
    def avg_expenses(self) -> float:
        _year = datetime.now().year
        _month = datetime.now().month

        # if  now().year == user.profile.year
        # calculate average till current month
        if self._year == _year:
            avg = 0.0
            arr = super().balance

            for x in range(_month):
                avg += arr[x]['expenses']

            return avg / _month

        # else return default average from super()
        avg = super().average
        return avg.get('expenses', 0.0)

    @property
    def income_data(self) -> list[float]:
        return self._balance.incomes.tolist()

    @property
    def expense_data(self) -> list[float]:
        return self._balance.expenses.tolist()

    @property
    def borrow_data(self) -> list[float]:
        return self._balance.borrow.tolist()

    @property
    def borrow_return_data(self) -> list[float]:
        return self._balance.borrow_return.tolist()

    @property
    def lend_data(self) -> list[float]:
        return self._balance.lend.tolist()

    @property
    def lend_return_data(self) -> list[float]:
        return self._balance.lend_return.tolist()

    @property
    def money_flow(self) -> list[float]:
        return self._balance.money_flow.tolist()

    def _calc_balance_and_money_flow(self, df: DF) -> DF:
        # calculate balance
        df['balance'] = df.incomes - df.expenses
        # calculate money_float
        df['money_flow'] = \
            0 \
            + df.balance + df.savings_close + df.borrow + df.lend_return \
            - df.savings - df.borrow_return - df.lend
        df['money_flow'].iloc[0] = df['money_flow'].iloc[0] + self.amount_start
        df['money_flow'] = df.money_flow.cumsum()

        return df
