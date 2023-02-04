import polars as pl
from polars import DataFrame as DF


class MakeDataFrame:
    def __init__(self, year: int, data: list[dict], columns: list = None, month: int = None):
        ''' Create pandas DataFrame from list of dictionaries

            Parameters
            ---------
            year: int

            data: list[dict]
                [{date, sum, exception_sum, title},]

            columns: list|tuple
                Optional.
                For insertation of additional columns

            month: int
                Optional.
                If value: DataFrame rows will be days of that month
                If no value: DataFrame rows will be 12 months
        '''
        self.year = year
        self.month = month
        self._data = data
        self._columns = columns

    @property
    def exceptions(self):
        df = self.create_data(sum_col_name='exception_sum')
        if df.is_empty():
            return df

        return df.select([
            pl.col('date'),
            pl.sum(pl.exclude('date')).alias('sum')
        ])

    @property
    def data(self):
        return self.create_data(sum_col_name='sum')

    def create_data(self, sum_col_name: str = 'sum') -> DF:
        if not self._data:
            return pl.DataFrame()

        df = pl.DataFrame(self._data)

        # grp = pl.col('date').dt.day() if self.month else pl.col('date').dt.month()

        df = (
            df
            .sort(['title', 'date'])
            .select(['date', 'title', sum_col_name])
            .pipe(self._cast_dtypes, sum_col_name=sum_col_name)
            .pipe(self._insert_missing_rows, sum_col_name=sum_col_name)
            # .groupby(['title', grp])
            # .agg(pl.col(sum_col_name).sum())
            # .sort(['title', 'date'])
            .pivot(values=sum_col_name, index='date', columns='title')
            .fill_null(0)
        )

        df = self._insert_missing_columns(df)
        df = self._sort_columns(df)
        return df

    def _cast_dtypes(self, df: DF, sum_col_name: str) -> pl.Expr:
        return (
            df.with_columns([
                pl.col('title').cast(pl.Categorical),
                pl.col(sum_col_name).cast(pl.Float32)]))

    def _insert_missing_columns(self, df: DF) -> DF:
        ''' Insert missing columns '''
        if not self._columns:
            return df

        cols_diff = set(self._columns) - set(df.columns)
        cols = [pl.lit(0).alias(col_name) for col_name in cols_diff]
        df = df.select([pl.all(), *cols])
        return df

    def _insert_missing_rows(self, df: DF, sum_col_name: str) -> pl.Expr:
        every = '1d' if self.month else '1mo'
        return (
            df
            .upsample(time_column='date', every=every, by="title", maintain_order=True)
            .with_columns([
                pl.col('title').forward_fill(),
                pl.col(sum_col_name).fill_null(0)])
        )

    def _sort_columns(self, df: DF) -> DF:
        cols = [pl.col(x) for x in sorted(df.columns[1:])]
        df = df.select([pl.col('date'), *cols])
        return df
