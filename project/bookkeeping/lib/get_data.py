from .data_frame import DataFrame


class GetObject(object):
    def __init__(self, model):
        self._model = model
        self._data = self._get_data()

    @property
    def df(self):
        return self._data

    def _get_data(self):
        try:
            qs = self._model.pd.to_dataframe(coerce_float=True)
        except Exception as e:
            qs = self._model.objects.all()

        f = DataFrame(qs).prepare()

        return f.df


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
