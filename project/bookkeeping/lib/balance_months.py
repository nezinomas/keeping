import pandas as pd


class BalanceMonths():
    def __init__(self, incomes, expenses, amount_start=0.0):
        try:
            amount_start = float(amount_start)
        except:
            amount_start = 0.0

        self._amount_start = amount_start
        self._balance = pd.DataFrame()

        if not incomes and not expenses:
            return

        self._calc(incomes, expenses)

    @property
    def balance(self):
        val = None
        balance = self._balance.copy()

        if not balance.empty:
            val = balance.to_dict('records')

        return val

    @property
    def amount_start(self):
        return self._amount_start

    @property
    def amount_end(self):
        val = 0.0

        if self.totals:
            val = self._amount_start + self.totals['balance']

        return val

    @property
    def balance_amount(self):
        val = 0.0

        if self.totals:
            val = self.totals['balance']

        return val

    @property
    def totals(self):
        val = None
        total = self._balance.copy()

        if not total.empty:
            total = total.sum()
            val = total.to_dict()

        return val

    @property
    def average(self):
        val = None
        avg = self._balance.copy()

        if not avg.empty:
            # replace 0.0 to None
            # average will be calculated only for months with non zero values
            avg.replace(0.0, pd.NaT, inplace=True)
            avg = avg.mean(skipna=True)

            val = avg.to_dict()

        return val

    def _convert_to_df(self, list_):
        year = list_[0]['date'].year

        df = pd.DataFrame(list_)

        # convert to float and datetime.date
        for col in df.columns:
            if col == 'date':
                df[col] = pd.to_datetime(df[col])
            else:
                df[col] = pd.to_numeric(df[col])

        df.set_index(df.date, inplace=True)

        # create empty DataFrame object with index containing all months
        date_range = pd.date_range(f'{year}', periods=12, freq='MS')
        data = pd.DataFrame(date_range, columns=['date'])
        data.set_index('date', inplace=True)

        # concat two dataframes
        df = pd.concat([data, df], axis=1).fillna(0.0)
        df.drop(['date'], axis=1, inplace=True)

        return df

    def _calc(self, incomes, expenses):
        incomes = self._convert_to_df(incomes)
        expenses = self._convert_to_df(expenses)

        df = incomes.join(
            expenses,
            how='left', lsuffix='_left', rsuffix='_right',
        ).reset_index()

        # calculate balance
        df.loc[:, 'balance'] = df.incomes - df.expenses

        #  calculate residual amount of money
        # for january
        df.at[0, 'residual'] = self._amount_start + df.at[0, 'balance']

        # for february:december
        for i in range(1, 12):
            df.at[i, 'residual'] = df.at[i, 'balance'] + df.at[i - 1, 'residual']

        # convert date from Timestamp to datetime.date
        df['date'] = df['date'].dt.date

        self._balance = df
