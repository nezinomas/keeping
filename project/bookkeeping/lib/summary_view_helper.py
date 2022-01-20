import json
from datetime import datetime
from typing import Dict, List

import numpy as np
from django.db.models.query import QuerySet


def chart_data(*args):
    items = {'categories': [], 'invested': [], 'profit': [], 'total': [], 'max': 0}

    for arr in args:
        if isinstance(arr, QuerySet):
            arr = list(arr)

        if not arr or not isinstance(arr, list):
            continue

        cnt = len(arr)
        for i in range(0, cnt):
            _y = arr[i]['year']
            _i= arr[i]['invested']
            _p = arr[i]['profit']
            _t = _i + _p

            if _y > datetime.now().year:
                continue

            if _i or _p:
                if _y not in items['categories']:
                    items['categories'].append(_y)
                    items['invested'].append(_i)
                    items['profit'].append(_p)
                    items['total'].append(_t)
                else:
                    ix = items['categories'].index(_y)  # category index
                    items['invested'][ix] += _i
                    items['profit'][ix] += _p
                    items['total'][ix] += _t

    # max value
    if items['profit'] or items['invested']:
        items['max'] = (max(items['profit']) + max(items['invested']))

    return items


def make_form_data_dict(form_data):
    _types = []
    _names = []
    _form_data_dict = {}
    _list = json.loads(form_data)

    # flatten list of dictionaries - form_data_list
    for field in _list:
        _field_name = field.get('name')
        _field_val = field.get('value')

        # expense type
        if _field_name == 'types' and not ':' in _field_val:
            _types.append(int(_field_val))
            continue

        # expense name
        if _field_name == 'types' and ':' in _field_val:
            _names.append(_field_val.split(':')[-1])
            continue

        # all other fields e.g. csrfmiddlewaretoke
        _form_data_dict[_field_name] = _field_val

    _form_data_dict['types'] = _types
    _form_data_dict['names'] = ','.join(_names)

    return _form_data_dict

class ExpenseCompareHelper():
    def __init__(self,
                 years: List,
                 types: List[Dict] = None,
                 names: List[Dict] = None,
                 remove_empty_columns: bool = None):

        self._years = years
        self._serries_data = []

        if not self._years:
            return

        self._serries_data += self._make_serries_data(types)
        self._serries_data += self._make_serries_data(names)

        if remove_empty_columns and self._serries_data:
            self._remove_empty_columns()

    @property
    def categories(self) -> List:
        return self._years

    @property
    def serries_data(self) -> List[Dict]:
        return self._serries_data

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
