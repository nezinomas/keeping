from typing import Dict

from django.utils.translation import gettext as _

from ..models import Book, BookTarget


class ChartReaded():
    _readed = 0
    _years = []
    _targets = []
    _data = []

    def __init__(self):
        self._readed = self._get_readed()

    @property
    def readed(self):
        return self._readed.count()

    def context(self):
        self._chart_data()

        return {
            'categories': self._years,
            'data': self._data,
            'targets': self._targets,
            'chart': 'chart_readed_books',
            'chart_title': _('Readed books'),
            'chart_column_color': '70, 171, 157'
        }

    def _chart_data(self):
        targets = self._targets_list()

        for readed in self._readed:
            year = readed['year']

            # chart categories
            self._years.append(year)

            # chart targets
            target = targets.get(year, 0)
            self._targets.append(target)

            # chart serries data
            data = {
                'y': readed['cnt'],
                'target': target,
            }
            self._data.append(data)

    def _get_readed(self):
        return Book.objects.readed()

    def _targets_list(self) -> Dict:
        qs = BookTarget.objects.items().values_list('year', 'quantity')

        # reverse keys and values
        arr = {k: v for k, v in qs}

        return arr
