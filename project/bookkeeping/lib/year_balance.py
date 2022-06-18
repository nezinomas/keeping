from datetime import datetime
from typing import Dict, List

from pandas import DataFrame as DF
from pandas import to_datetime

from ...core.lib.balance_base import BalanceBase, df_months_of_year


class YearBalance(BalanceBase):
    columns = (
        'incomes',
        'expenses',
        'savings',
        'savings_close',
        'borrow',
        'borrow_return',
        'lend',
        'lend_return'
    )

    def __init__(self,
                 year: int,
                 data: Dict[str, Dict],
                 amount_start: float = 0.0):

        '''
        year: int

        data: {'incomes': [{'date': datetime.date(), 'sum': Decimal()}, ... ]}

        amount_start: year start worth amount

        awailable keys in data: incomes, expenses, savings, savings_close, borrow, borrow_return, lend, lend_return
        '''

        super().__init__()

        try:
            amount_start = float(amount_start)
        except TypeError:
            amount_start = 0.0

        self._amount_start = amount_start
        self._year = year

        self._balance = self._make_df(year=year, data=data)
        self._balance = self._calc(self._balance)

    @property
    def amount_start(self) -> float:
        return self._amount_start

    @property
    def amount_end(self) -> float:
        try:
            val = self._balance['money_flow'].values[-1]
        except KeyError:
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

            for x in range(0, _month):
                avg += arr[x]['expenses']

            return avg / _month

        # else return default average from super()
        avg = super().average
        return avg.get('expenses', 0.0)

    @property
    def income_data(self) -> List[float]:
        rtn = []
        if 'incomes' in self._balance:
            rtn = self._balance.incomes.tolist()

        return rtn

    @property
    def expense_data(self) -> List[float]:
        rtn = []
        if 'expenses' in self._balance:
            rtn = self._balance.expenses.tolist()

        return rtn

    @property
    def borrow_data(self) -> List[float]:
        rtn = []
        if 'borrow' in self._balance:
            rtn = self._balance.borrow.tolist()

        return rtn

    @property
    def borrow_return_data(self) -> List[float]:
        rtn = []
        if 'borrow_return' in self._balance:
            rtn = self._balance.borrow_return.tolist()

        return rtn

    @property
    def lend_data(self) -> List[float]:
        rtn = []
        if 'lend' in self._balance:
            rtn = self._balance.lend.tolist()

        return rtn

    @property
    def lend_return_data(self) -> List[float]:
        rtn = []
        if 'lend_return' in self._balance:
            rtn = self._balance.lend_return.tolist()

        return rtn

    @property
    def money_flow(self) -> List[float]:
        rtn = []
        if 'money_flow' in self._balance:
            rtn = self._balance.money_flow.tolist()

        return rtn

    def _make_df(self, year: int, data: Dict[str, Dict]) -> DF:
        df = df_months_of_year(year)

        # create columns with 0 values
        for col in self.columns:
            df[col] = 0.0

        df['balance'] = 0
        df['money_flow'] = 0

        if not data:
            return df

        for col_name, data_arr in data.items():
            if not data_arr:
                continue

            # copy values from input arrays to df
            for row in data_arr:
                df.at[to_datetime(row['date']), col_name] = float(row['sum'])

        return df

    def _calc(self, df: DF) -> DF:
        # calculate balance
        df['balance'] = df.incomes - df.expenses

        #  calculate money_flow
        for i in range(0, 12):
            idx = df.index[i]
            idx_prev = df.index[i - 1]

            val = (
                0.0
                + df.loc[idx, 'balance']
                + df.loc[idx, 'savings_close']
                - df.loc[idx, 'savings']
                + df.loc[idx, 'borrow']
                - df.loc[idx, 'borrow_return']
                - df.loc[idx, 'lend']
                + df.loc[idx, 'lend_return']
            )

            cell = (idx, 'money_flow')

            # january
            if i == 0:
                df.loc[cell] = (
                    val
                    + self._amount_start
                )
            # february - december
            else:
                df.loc[cell] = (
                    val
                    + df.loc[idx_prev, 'money_flow']
                )

        return df
