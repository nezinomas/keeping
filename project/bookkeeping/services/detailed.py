import itertools
import operator
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
        start = date(year, 1, 1)
        end = date(year, 12, 1)

        for i in data:
            j = (i["type_title"], i["title"])
            if j in maps:
                continue

            maps.add(j)

            si = {
                "date": start,
                "title": i["title"],
                "type_title": i["type_title"],
                "sum": 0,
            }
            ei = {
                "date": end,
                "title": i["title"],
                "type_title": i["type_title"],
                "sum": 0,
            }

            data.extend((si, ei))
        return data

    def _create_context(self, data, categories, name = None):
        context = []

        df = self._create_df(data)
        df = df.partition_by("type_title")

        for i, t in enumerate(categories):
            da = df[i].partition_by("title")

            data = {
                "name": name + t if name else t,
                "items": [],
                "total": df[i]["total_col"].sum(),
                "total_col": [],
                "total_row": da[0]["total_row"].to_list(),
            }

            for d in da:
                row = {"title": d["title"][0], "data": d["sum"].to_list()}
                data["items"].append(row)
                data["total_col"].append(d["total_col"].sum())

            context.append(data)
        return context

    def _create_df(self, arr):
        pl.Config.set_tbl_rows(100)
        df = pl.DataFrame(arr).sort(["date", "type_title", "title"])
        df = (
            df
            .upsample(
                time_column="date",
                every="1mo",
                by=["type_title", "title"],
                maintain_order=True,
            )
            .lazy()
            .select(
                [
                    pl.col.date,
                    pl.col.sum.fill_null(0),
                    pl.col.title.forward_fill(),
                    pl.col.type_title.forward_fill(),
                ]
            )
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
