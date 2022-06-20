from typing import Dict, List

import numpy as np

from ...core.lib.date import years
from ...expenses.models import Expense


class ChartSummaryExpensesService():
    def __init__(self,
                 types: List[Dict],
                 names: List[Dict] = None,
                 remove_empty_columns: bool = None):

        self._years = self._get_years()
        self._serries_data = []

        if not self._years:
            return

        if types:
            data = self._get_type_sum_by_year(types)
            self._serries_data += self._make_serries_data(data)


        self._serries_data += self._make_serries_data(names)

        if remove_empty_columns and self._serries_data:
            self._remove_empty_columns()

        self._calc_totals()

    @property
    def categories(self) -> List:
        return self._years

    @property
    def serries_data(self) -> List[Dict]:
        return self._serries_data

    @property
    def total_col(self) -> Dict:
        return self._total_col

    @property
    def total_row(self) -> List:
        return self._total_row

    @property
    def total(self) -> float:
        return self._total

    def _get_years(self) -> List:
        return years()[:-1]

    def _get_type_sum_by_year(self, expense_type: List) -> List[Dict]:
        return Expense.objects.sum_by_year_type(expense_type)

    def _make_serries_data(self, data):
        _items = []

        if not data:
            return _items

        _titles = []
        _titles_hooks = {}
        _years_hooks = {v: k for k, v in enumerate(self._years)}

        for i in data:
            _title = i['title']

            _root = i.get('root')
            if _root:
                _title = f'{_root}/{_title}'

            _sum = float(i['sum'])
            _year = i['year']
            _year_index = _years_hooks.get(_year)

            if _year_index is None:
                continue

            if _title not in _titles:
                _titles.append(_title)
                _items.append({
                    'name': _title,
                    'data': [0.0] * len(self._years)
                })
                _titles_hooks = {v: k for k, v in enumerate(_titles)}

            _title_index = _titles_hooks[_title]
            _items[_title_index]['data'][_year_index] = _sum

        return _items

    def _remove_empty_columns(self):
        _matrix = np.array([x['data'] for x in self._serries_data])
        _idx = np.argwhere(np.all(_matrix[..., :] == 0, axis=0))
        _clean = np.delete(_matrix, _idx, axis=1).tolist()

        # year list
        # flatten and reverse indexes
        _idx = _idx.flatten().tolist()[::-1]
        for _i in _idx:
            del self._years[_i]

        # clean serries data
        for _i, _list in enumerate(_clean):
            self._serries_data[_i]['data'] = _list

    def _calc_totals(self):
        self._total = 0.0
        self._total_col = {}
        self._total_row = []

        if self._serries_data:
            _matrix = np.array([x['data'] for x in self._serries_data])
            _col = _matrix.sum(axis=1)
            _row = _matrix.sum(axis=0)

            for _i, _v in enumerate(_col):
                self._total_col[self._serries_data[_i]['name']] = _v

            self._total_row = _row.tolist()

            self._total = _row.sum()
