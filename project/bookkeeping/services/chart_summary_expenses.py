from dataclasses import dataclass, field

import numpy as np

from ...expenses.models import Expense


@dataclass
class ChartSummaryExpensesServiceData:
    form_data: list[dict] = field(default_factory=list)
    data: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        types, names = self._parse_form_data(self.form_data)

        if types:
            self.data += self._get_types(types)

        if names:
            self.data += self._get_names(names)

    def _parse_form_data(self, data):
        types, names = [], []

        if data:
            for x in data:
                if ':' in x:
                    names.append(x.split(':')[1])
                else:
                    types.append(x)

        return types, names

    def _get_types(self, types: list) -> list[dict]:
        return Expense.objects.sum_by_year_type(types)

    def _get_names(self, names: list) -> list[dict]:
        return Expense.objects.sum_by_year_name(names)


@dataclass
class ChartSummaryExpensesService:
    data: ChartSummaryExpensesServiceData = field(default_factory=list)

    categories: list = field(init=False, default_factory=list)
    total: float = field(init=False, default=0.0)
    total_col: dict = field(init=False, default_factory=dict)
    total_row: list = field(init=False, default_factory=list)
    serries_data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        if not self.data.data:
            return

        self.categories = sorted({r['year'] for r in self.data.data})
        self.serries_data = self._make_serries_data(self.categories, self.data.data)

        self._calc_totals(self.serries_data)

    def _make_serries_data(self, categories, data):
        _items = []
        _titles = []
        _titles_hooks = {}
        _years_hooks = {v: k for k, v in enumerate(categories)}

        for i in data:
            _title = i['title']

            if _root := i.get('root'):
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
                    'data': [0.0] * len(categories)
                })
                _titles_hooks = {v: k for k, v in enumerate(_titles)}

            _title_index = _titles_hooks[_title]
            _items[_title_index]['data'][_year_index] = _sum

        return _items

    def _calc_totals(self, data):
        _matrix = np.array([x['data'] for x in data])
        _col = _matrix.sum(axis=1)
        _row = _matrix.sum(axis=0)

        for _i, _v in enumerate(_col):
            self.total_col[data[_i]['name']] = _v

        self.total_row = _row.tolist()

        self.total = _row.sum()
