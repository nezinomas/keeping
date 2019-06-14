import pandas as pd
from django.db.models.query import QuerySet
from django_pandas.io import read_frame
from decimal import Decimal


class DataFrame(object):
    def __init__(self, query_set=None):
        self.__df = pd.DataFrame()

        if query_set is not None:
            if isinstance(query_set, QuerySet):
                self._df = (
                    read_frame(query_set, coerce_float=True).
                    reset_index(drop=True)
                )

            if isinstance(query_set, pd.DataFrame):
                self.df = query_set

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        self._df = df

    def prepare(self):
        if 'date' in self._df.columns:
            self._df['date'] = pd.to_datetime(self._df['date'])
            self._df['year_m'] = self._df['date'].apply(lambda x: x.strftime('%Y-%m'))

        return self
