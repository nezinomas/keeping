from dataclasses import dataclass, field
from datetime import date

import polars as pl
from django.utils.translation import gettext as _

from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...savings.models import Saving


@dataclass
class DetailerServiceData:
    year: int
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    savings: list[dict] = field(init=False, default_factory=list)
    expenses_types: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = list(Income.objects.sum_by_month_and_type(self.year))
        self.savings = list(Saving.objects.sum_by_month_and_type(self.year))
        self.expenses = list(Expense.objects.sum_by_month_and_name(self.year))
        self.expenses_types = list(
            ExpenseType.objects.items().values_list("title", flat=True)
        )


class DetailedService:
    def __init__(self, data: DetailerServiceData):
        self._year = data.year
        self._incomes = data.incomes
        self._expenses = data.expenses
        self._savings = data.savings
        self._expenses_types = data.expenses_types
        self._expenses_types.sort()

    def incomes_context(self) -> list[dict]:
        name = _('Incomes')
        data = __class__.insert_type(name, self._incomes)
        data = __class__.modify_data(self._year, data)
        return self._create_context(data, [name])

    def savings_context(self) -> list[dict]:
        name = _('Savings')
        data = __class__.insert_type(name, self._savings)
        data = __class__.modify_data(self._year, data)
        return self._create_context(data, [name])

    def expenses_context(self) -> list[dict]:
        data = __class__.modify_data(self._year, self._expenses)
        name = f'{_("Expenses")} / '
        return self._create_context(data, self._expenses_types, name)

    @staticmethod
    def insert_type(name, data):
        return [x | {"type_title": name} for x in data]

    @staticmethod
    def modify_data(year, data):
        maps = set()
        arr = []
        for i in data:
            title_map = (i["type_title"], i["title"])
            if title_map in maps:
                continue

            maps.add(title_map)

            arr += [{
                    "date": date(year, mm, 1),
                    "title": i["title"],
                    "type_title": i["type_title"],
                    "sum": 0,
                } for mm in range(1, 13)]

        data.extend(arr)
        return data

    def _create_context(self, data, categories, name = None):
        context = []

        if not data:
            return context

        data = self._create_df(data)

        for category in categories:
            context_item = {
                "name": name + category if name else category,
                "items": [],
                "total": 0,
                "total_col": [],
                "total_row": [],
            }

            df = data.filter(pl.col.type_title == category)
            for d in df.partition_by("title"):
                context_item["items"] += [{"title": d["title"][0], "data": d["sum"].to_list()}]
                context_item["total"] += d["total_col"].sum()
                context_item["total_col"] += [d["total_col"].sum()]
                context_item["total_row"] = d["total_row"].to_list()

            context.append(context_item)
        return context

    def _create_df(self, arr):
        df = (
            pl.DataFrame(arr)
            .lazy()
            .group_by([pl.col.date, pl.col.type_title, pl.col.title])
            .agg(pl.col.sum.sum())
            .with_columns(
                pl.col.sum.sum()
                .over([pl.col.date, pl.col.type_title])
                .alias("total_row")
            )
            .with_columns(
                pl.col.sum.sum()
                .over([pl.col.date, pl.col.type_title, pl.col.title])
                .alias("total_col")
            )
            .sort([pl.col.type_title, pl.col.title, pl.col.date])
        )
        return df.collect()
