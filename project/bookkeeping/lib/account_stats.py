import pandas as pd


class AccountStats():
    def __init__(self, account_stats, account_worth):
        self._balance = pd.DataFrame()

        if not account_stats or account_stats is None:
            return

        self._prepare_balance(account_stats, account_worth)
        self._calc_balance()

    @property
    def balance(self):
        val = []
        balance = self._balance.copy()

        if not balance.empty:
            balance.reset_index(inplace=True)
            val = balance.to_dict('records')

        return val

    @property
    def totals(self):
        val = []
        balance = self._balance.copy()

        if not balance.empty:
            val = balance.sum().to_dict()

        return val

    @property
    def balance_start(self):
        val = 0.0

        if self.totals:
            val = self.totals['past']

        return val

    def _prepare_balance(self, account_stats, account_worth):
        df = pd.DataFrame(account_stats).set_index('title')

        if account_worth:
            _worth = pd.DataFrame(account_worth).set_index('title')
            df = df.join(_worth)
        else:
            df.loc[:, 'have'] = 0.0

        # convert to float
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])

        self._balance = df

    def _calc_balance(self):
        self._balance.loc[:, 'delta'] = (
            self._balance['have'] - self._balance['balance']
        )
