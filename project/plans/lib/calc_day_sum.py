from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from typing import Union

import polars as pl
from django.db.models import F
from django.utils.translation import gettext as _
from polars import DataFrame as DF

from ...core.lib.date import monthlen, monthname, monthnames
from ..models import (DayPlan, ExpensePlan, IncomePlan, NecessaryPlan,
                      SavingPlan)


@dataclass
class PlanCollectData:
    year: int = 1970
    month: int = 0

    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    savings: list[dict] = field(init=False, default_factory=list)
    days: list[dict] = field(init=False, default_factory=list)
    necessary: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        month_names = monthnames()

        self.incomes = IncomePlan.objects.year(self.year).values(*month_names)

        self.expenses = ExpensePlan.objects.year(self.year).values(
            *month_names,
            necessary=F("expense_type__necessary"),
            title=F("expense_type__title")
        )

        self.savings = SavingPlan.objects.year(self.year).values(*month_names)
        self.days = DayPlan.objects.year(self.year).values(*month_names)
        self.necessary = NecessaryPlan.objects.year(self.year).values(*month_names).annotate(title=F("expense_type__title"))


class PlanCalculateDaySum:
    def __init__(self, data: PlanCollectData):
        self.std_columns = monthnames()

        self._data = data
        self._year = data.year
        self._df = self._calc_df()

    @property
    def incomes(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "incomes")
        return self._return_data(data)

    @property
    def savings(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "savings")
        return self._return_data(data)

    @property
    def expenses_free(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "expenses_free")
        return self._return_data(data)

    @property
    def expenses_necessary(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "expenses_necessary")
        return self._return_data(data)

    @property
    def expenses_full(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "expenses_full")
        return self._return_data(data)

    @property
    def expenses_remains(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "expenses_remains")
        return self._return_data(data)

    @property
    def day_calced(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "day_calced")
        return self._return_data(data)

    @property
    def day_input(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "day_input")
        return self._return_data(data)

    @property
    def remains(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "remains")
        return self._return_data(data)

    @property
    def necessary(self) -> dict[str, float]:
        data = self._df.filter(pl.col("name") == "necessary")
        return self._return_data(data)

    @property
    def plans_stats(self):
        Items = namedtuple("Items", ["type", *self.std_columns])

        return [
            Items(type=_("Necessary expenses"), **self.expenses_necessary),
            Items(type=_("Remains for everyday"), **self.expenses_free),
            Items(type=_("Full expenses"), **self.expenses_full),
            Items(type=f"Avg {_('Incomes')} - {_('Full expenses')}", **self.expenses_remains),
            Items(type=_("Sum per day, max possible"), **self.day_calced),
            Items(type=_("Residual"), **self.remains),
        ]

    @property
    def targets(self) -> dict[str, float]:
        rtn = defaultdict(int)

        if not self._data.month:
            return rtn

        month = monthname(self._data.month)
        data = [*self._data.expenses, *self._data.necessary]
        for item in data:
            title = item.get("title", "unknown")
            val = item.get(month, 0) or 0
            rtn[title] += val

        return rtn

    def _return_data(self, data: Union[pl.Series, float]) -> Union[dict, float]:
        """If data is polars Serries convert data to dictionary"""
        select = monthname(self._data.month) if self._data.month else self.std_columns
        data = data.select(select)
        return data[0, 0] if self._data.month else data.to_dicts()[0]

    def _create_df(self) -> DF:
        expenses_necessary = filter(lambda x: x["necessary"], self._data.expenses)
        expenses_free = filter(lambda x: not x["necessary"], self._data.expenses)

        df_data = {
            "month_len": [monthlen(self._year, x) for x in self.std_columns],
            "incomes": self._sum_dicts(self._data.incomes),
            "savings": self._sum_dicts(self._data.savings),
            "day_input": self._sum_dicts(self._data.days),
            "necessary": self._sum_dicts(self._data.necessary),
            "expenses_necessary": self._sum_dicts(list(expenses_necessary)),
            "expenses_free": self._sum_dicts(list(expenses_free)),
        }
        return pl.DataFrame(df_data)

    def _sum_dicts(self, data: list[dict]) -> list[int]:
        return [
            sum(map(lambda x: x.get(month) or 0, data)) for month in self.std_columns
        ]

    def _calc_df(self) -> None:
        df = self._create_df()

        return (
            df.lazy()
            .with_columns(
                expenses_necessary=(
                    pl.lit(0)
                    + pl.col("expenses_necessary")
                    + pl.col("savings")
                    + pl.col("necessary")
                )
            )
            .with_columns(expenses_full=(pl.col("expenses_necessary") + pl.col("expenses_free")))
            .with_columns(day_calced=(pl.col("expenses_free") / pl.col("month_len")))
            .with_columns(
                remains=(
                    pl.col("expenses_free")
                    - (pl.col("day_input") * pl.col("month_len"))
                )
            )
            .with_columns(incomes_avg=pl.col.incomes.mean())
            .with_columns(
                expenses_remains=(pl.col.incomes_avg - pl.col.expenses_full)
            )
            .collect()
            .transpose(
                include_header=True, header_name="name", column_names=self.std_columns
            )
        )
