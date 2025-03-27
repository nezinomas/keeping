import itertools as it
from dataclasses import dataclass, field
from datetime import date

import polars as pl
from django.utils.text import slugify
from django.utils.translation import gettext as _

from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...savings.models import Saving


@dataclass
class Data:
    year: int
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    savings: list[dict] = field(init=False, default_factory=list)
    expenses_types: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = Income.objects.sum_by_month_and_type(self.year)
        self.savings = Saving.objects.sum_by_month_and_type(self.year)
        self.expenses = Expense.objects.sum_by_month_and_name(self.year)
        self.expenses_types = ExpenseType.objects.items().values_list("title", flat=True)


class Service:
    def __init__(self, data: Data):
        self._year = data.year
        self._incomes = list(data.incomes)
        self._expenses = list(data.expenses)
        self._savings = list(data.savings)
        self._expenses_types = sorted(data.expenses_types)

    def incomes_context(self) -> list[dict]:
        name = _("Incomes")
        data = __class__.insert_type(name, self._incomes)
        data = __class__.modify_data(self._year, data)
        return self._create_context(data, [name])

    def savings_context(self) -> list[dict]:
        name = _("Savings")
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

            arr += [
                {
                    "date": date(year, month, 1),
                    "title": i["title"],
                    "type_title": i["type_title"],
                    "sum": 0,
                }
                for month in range(1, 13)
            ]

        data.extend(arr)
        return data

    def _create_context(self, data, categories, name=""):
        context = []
        if not data:
            return context

        df = self._create_df(data)
        for category in categories:
            if context_item := self._create_context_item(df, category, name):
                context.append(context_item)
        return context

    def _create_context_item(self, df, category, name):
        context_item = {
            "name": name + category,
            "slug": slugify(category),
            "items": [],
            "total": 0,
            "total_col": [],
            "total_row": [],
        }

        df_category = df.filter(pl.col.type_title == category)
        if df_category.is_empty():
            return None

        for df_part in df_category.partition_by("title"):
            total_col = df_part["total_col"].sum()
            context_item["total"] += total_col
            context_item["total_col"] += [total_col]
            context_item["total_row"] = df_part["total_row"].to_list()
            context_item["items"] += [
                {"title": df_part["title"][0], "data": df_part["sum"].to_list()}
            ]
        return context_item

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


def load_service(year: int) -> dict:
    data = Data(year)
    obj = Service(data)

    return {
        "object_list": it.chain(
            obj.incomes_context(), obj.savings_context(), obj.expenses_context()
        ),
    }
