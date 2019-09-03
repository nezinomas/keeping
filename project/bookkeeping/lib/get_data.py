import pandas as pd
from django.db import models


class GetObject(object):
    def __init__(self, model):
        self._model = model
        self._data = self._get_data()

    @property
    def df(self):
        return self._data

    def _get_fields(self):
        """
        Returns:
        tuple of (values_list, dataframe_columns)

        values_list - list of model fields for QuerySet.values_list()

        dataframe_columns - list of model fields for pandas DataFrame
        """

        dataframe_columns = []
        values_list = []
        fields = self._model._meta.get_fields()
        for f in fields:
            if isinstance(f, models.ManyToOneRel):
                continue

            if (f.many_to_one):
                values_list.append(f.name+'__title')
            else:
                values_list.append(f.name)

            dataframe_columns.append(f.name)

        return values_list, dataframe_columns

    def _get_data(self):
        try:
            qs = self._model.objects.items()
        except Exception as e:
            qs = self._model.objects.all()

        values_list, dataframe_columns = self._get_fields()

        _df = list(qs.values_list(*values_list))

        _df = pd.DataFrame(_df, columns=dataframe_columns)

        return self._prepare(_df)

    def _prepare(self, _df):
        if 'date' in _df.columns:
            _df['date'] = pd.to_datetime(_df['date'])
            _df['year_m'] = _df['date'].apply(
                lambda x: x.strftime('%Y-%m'))

        if 'price' in _df.columns:
            _df['price'] = pd.to_numeric(_df['price'])

        if 'fee' in _df.columns:
            _df['fee'] = pd.to_numeric(_df['fee'])

        _df.set_index(['id'])

        return _df


class GetObjects(object):
    def __init__(self, model_list):
        self._models = model_list
        self._data = self._get_data()

    @property
    def data(self):
        return self._data

    def _get_data(self):
        items = {}
        for model in self._models:
            items[model._meta.model_name] = GetObject(model).df

        return items
