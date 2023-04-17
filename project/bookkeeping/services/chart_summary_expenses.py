import itertools
import operator
from dataclasses import dataclass, field

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
                if ":" in x:
                    names.append(x.split(":")[1])
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
    total_col: dict = field(init=False, default_factory=dict)
    total_row: list = field(init=False, default_factory=list)
    serries_data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        if not self.data.data:
            return

        self.categories = sorted({r["year"] for r in self.data.data})
        self.serries_data = self._make_serries_data(self.categories, self.data.data)

        self._calc_total_column(self.serries_data)
        self._calc_total_row(self.serries_data)

    @property
    def total(self):
        return sum(self.total_row)

    def _make_serries_data(self, categories, data):
        _items = []
        _year_hooks = {v: k for k, v in enumerate(categories)}

        # sort data by title and year
        data = sorted(data, key=operator.itemgetter("title", "year"))

        for title, group in itertools.groupby(data, key=operator.itemgetter("title")):
            # make empty data list for each title
            _item = {"name": title, "data": [0] * len(categories)}

            # fill data
            for x in group:
                _year = x["year"]
                _sum = float(x["sum"])
                _year_idx = _year_hooks.get(_year)
                _item["data"][_year_idx] = _sum

            _items.append(_item)

        return _items

    def _calc_total_column(self, data):
        matrix = [x["data"] for x in data]
        col = [sum(idx) for idx in matrix]

        for i, val in enumerate(col):
            self.total_col[data[i]["name"]] = val

    def _calc_total_row(self, data):
        matrix = [x["data"] for x in data]
        self.total_row = [sum(idx) for idx in zip(*matrix)]
