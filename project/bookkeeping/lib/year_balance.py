from datetime import datetime

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
        'lend_return',
        'balance',
        'money_flow',
    )

    def __init__(self,
                 year: int,
                 data: dict[str, dict],
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
        self._balance = self._calc_balance_and_money_flow(self._balance)

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

    def _make_df(self, year: int, data: dict[str, dict]) -> DF:
        df = df_months_of_year(year)

        # create columns with 0 values
        for col in self.columns:
            df[col] = 0.0

        if not data or not any(data.values()):
            return df

        for col_name, data_arr in data.items():
            if not data_arr:
                continue

            if col_name not in self.columns:
                continue

            # copy values from input arrays to df
            for row in data_arr:
                df.at[to_datetime(row['date']), col_name] = float(row['sum'])

        return df

    def _calc_balance_and_money_flow(self, df: DF) -> DF:
        # calculate balance
        df['balance'] = df.incomes - df.expenses

        #  calculate money_flow
        for i in range(12):
            idx = df.index[i]
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
            else:
                idx_prev = df.index[i - 1]

                df.loc[cell] = (
                    val
                    + df.loc[idx_prev, 'money_flow']
                )

        return df
