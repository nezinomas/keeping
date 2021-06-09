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
                 amount_start: float = 0.0):

        '''
        year: int

        incomes: [{'date': datetime.date(), 'sum': Decimal()}, ... ]

        expenses: [{'date': datetime.date(), 'sum': Decimal()}, ... ]

        savings: [{'date': datetime.date(), 'sum': Decimal()}, ... ]

        savings_close: [{'date': datetime.date(), 'sum': Decimal()}, ... ]

        amount_start: year start worth amount
        '''

        super().__init__()

        try:
            amount_start = float(amount_start)
        except TypeError:
            amount_start = 0.0

        self._amount_start = amount_start

        if not incomes and not expenses:
            return

        self._balance = self._make_df(
            year=year,
            incomes=incomes,
            expenses=expenses,
            savings=savings,
            savings_close=savings_close)

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
                 savings_close: List[Dict]) -> DF:

        df = df_months_of_year(year)

        # append necessary columns
        df.loc[:, 'incomes'] = 0.0
        df.loc[:, 'expenses'] = 0.0
        df.loc[:, 'money_flow'] = 0.0
        df.loc[:, 'balance'] = 0.0
        df.loc[:, 'savings'] = 0.0
        df.loc[:, 'savings_close'] = 0.0
        df.loc[:, 'money_flow'] = self._amount_start

        # copy incomes values, convert Decimal to float
        for d in incomes:
            df.at[to_datetime(d['date']), 'incomes'] = float(d['sum'])

        # copy expenses values, convert Decimal to float
        for d in expenses:
            df.at[to_datetime(d['date']), 'expenses'] = float(d['sum'])

        if savings:
            # copy savings values, convert Decimal to float
            for d in savings:
                df.at[to_datetime(d['date']), 'savings'] = float(d['sum'])

        if savings_close:
            # copy savings values, convert Decimal to float
            for d in savings_close:
                df.at[to_datetime(d['date']), 'savings_close'] = float(d['sum'])

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
