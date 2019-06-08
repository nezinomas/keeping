from .data_frame import DataFrame


class GetData(object):
    def __init__(self, model):
        self._model = model
        self._data = self._get_data()

    @property
    def data(self):
        return self._data

    def _get_data(self):
        qs = self._model.objects.all()
        f = DataFrame(qs).prepare()

        return f.df
