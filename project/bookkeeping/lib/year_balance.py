from datetime import datetime
from typing import Dict, List

from pandas import DataFrame as DF
from pandas import to_datetime

from ...core.lib.balance_base import BalanceBase, df_months_of_year


class YearBalance(BalanceBase):
    def __init__(self,
                 year: int,
                 incomes: List[Dict],
                 expenses: List[Dict],
                 savings: List[Dict] = None,
                 savings_close: List[Dict] = None,
                 borrow: List[Dict] = None,
                 borrow_return: List[Dict] = None,
                 debt: List[Dict] = None,
                 debt_return: List[Dict] = None,
                 amount_start: float = 0.0):

        '''
        year: int
        incomes: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        expenses: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        savings: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        savings_close: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        borrow: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        borrow_return: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        debt: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        debt_return: [{'date': datetime.date(), 'sum': Decimal()}, ... ]
        amount_start: year start worth amount
        '''

        super().__init__()

        try:
            amount_start = float(amount_start)
        except TypeError:
            amount_start = 0.0

        self._amount_start = amount_start
        self._year = year
        # ToDo: delete after some time (commented on 2021.08.26)
        # if not incomes and not expenses:
        #     return

        self._balance = self._make_df(
            year=year,
            incomes=incomes,
            expenses=expenses,
            savings=savings,
            savings_close=savings_close,
            borrow=borrow,
            borrow_return=borrow_return,
            debt=debt,
            debt_return=debt_return,
        )

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
    def debt_data(self) -> List[float]:
        rtn = []
        if 'debt' in self._balance:
            rtn = self._balance.debt.tolist()

        return rtn

    @property
    def debt_return_data(self) -> List[float]:
        rtn = []
        if 'debt_return' in self._balance:
            rtn = self._balance.debt_return.tolist()

        return rtn

    @property
    def money_flow(self) -> List[float]:
        rtn = []
        if 'money_flow' in self._balance:
            rtn = self._balance.money_flow.tolist()

        return rtn

    def _make_df(self,
                 year: int,
                 incomes: List[Dict],
                 expenses: List[Dict],
                 savings: List[Dict],
                 savings_close: List[Dict],
                 borrow: List[Dict],
                 borrow_return: List[Dict],
                 debt: List[Dict],
                 debt_return: List[Dict]) -> DF:

        df = df_months_of_year(year)

        # append necessary columns
        dict = {
            'incomes': incomes,
            'expenses': expenses,
            'savings': savings,
            'savings_close': savings_close,
            'borrow': borrow,
            'borrow_return': borrow_return,
            'debt': debt,
            'debt_return': debt_return,
        }

        for name, arr in dict.items():
            # create column and assign 0 for all cells
            df.loc[:, name] = 0.0
            if arr:
                # copy values from input arrays to df
                for d in arr:
                    df.at[to_datetime(d['date']), name] = float(d['sum'])

        df.loc[:, 'balance'] = 0.0
        df.loc[:, 'money_flow'] = self._amount_start

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
                - df.loc[idx, 'borrow']
                + df.loc[idx, 'borrow_return']
                + df.loc[idx, 'debt']
                - df.loc[idx, 'debt_return']
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
