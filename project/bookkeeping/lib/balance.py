from datetime import date

import janitor
import pandas as pd
from pandas import DataFrame as DF


def create_data(data: list[dict], types: list, sum_column: str = 'sum', option: str = 'month') -> DF:
    year = data[0]['date'].year
    month = data[0]['date'].month
    df = DF(data).remove_columns(['exception_sum']).to_datetime('date')
    df[sum_column] = df[sum_column].apply(pd.to_numeric, downcast='float')
    # groupby month or day and sum
    grp = df.date.dt.month if option == 'month' else df.date.dt.day
    df = df.groupby(['title', grp])['sum'].sum()
    # modifie df: unstack, transpose, row to col names
    df = df.unstack().reset_index().T.reset_index()
    df.columns = df.iloc[0] # first row values -> to columns names
    df = df.drop(0)  # remove first row
    df = df.rename(columns={'title': 'date'})  # rename column

    # create missing columns
    df[[*set(types) - set(df.columns)]] = 0.0
    df = df[sorted(df.columns)]

    # create missing rows
    if option == 'month':
        df['date'] = pd.to_datetime(df['date'].apply(lambda x: date(year, x, 1)))
        new_dates = {'date': pd.date_range(f'{year}', periods=12, freq='MS')}
    else:
        df['date'] = pd.to_datetime(df['date'].apply(lambda x: date(year, month, x)))
        new_dates = {'date': pd.date_range(
            start=pd.Timestamp(year, month, 1),
            end=pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0),
            freq='D'
        )}

    df = df.complete(new_dates, fill_value=0.0).set_index('date')

    print(f'\nF >>>>>>\n{df}\n')
    return df
