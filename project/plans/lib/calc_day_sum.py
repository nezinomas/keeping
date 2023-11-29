import itertools
from collections import namedtuple
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
        self.incomes = IncomePlan.objects.year(self.year).values(*monthnames())

        self.expenses = ExpensePlan.objects.year(self.year).values(
            *monthnames(),
            necessary=F("expense_type__necessary"),
            title=F("expense_type__title")
        )

        self.savings = SavingPlan.objects.year(self.year).values(*monthnames())
        self.days = DayPlan.objects.year(self.year).values(*monthnames())
        self.necessary = NecessaryPlan.objects.year(self.year).values(*monthnames())


class PlanCalculateDaySum:
    std_columns = (
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    )

    def __init__(self, data: PlanCollectData):
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
        dicts = [
            dict({"type": _("Necessary expenses")}, **self.expenses_necessary),
            dict({"type": _("Remains for everyday"), **self.expenses_free}),
            dict({"type": _("Sum per day, max possible")}, **self.day_calced),
            dict({"type": _("Residual")}, **self.remains),
        ]
        # list of dictionaries convert to list of objects
        return [namedtuple("Items", item.keys())(*item.values()) for item in dicts]

    @property
    def targets(self) -> dict[str, float]:
        rtn = {}

        if not self._data.month:
            return rtn

        month = monthname(self._data.month)
        arr = self._data.expenses

        for item in arr:
            val = item.get(month, 0) or 0
            rtn[item.get("title", "unknown")] = float(val)

        return rtn

    def _return_data(self, data: Union[pl.Series, float]) -> Union[dict, float]:
        """If data is polars Serries convert data to dictionary"""
        select = monthname(self._data.month) if self._data.month else self.std_columns
        data = data.select(select)
        return data[0, 0] if self._data.month else data.to_dicts()[0]

    def _create_df(self) -> DF:
        expenses_necessary = filter(lambda item: item['necessary'], self._data.expenses)
        expenses_free = filter(lambda item: not item['necessary'], self._data.expenses)

        df_data = {
            "month_len": [int(monthlen(self._year, x)) for x in self.std_columns],
            "incomes": self._sum_dicts(self._data.incomes),
            "savings": self._sum_dicts(self._data.savings),
            "day_input": self._sum_dicts(self._data.days),
            "necessary": self._sum_dicts(self._data.necessary),
            "expenses_necessary": self._sum_dicts(expenses_necessary),
            "expenses_free": self._sum_dicts(expenses_free),
        }
        return pl.DataFrame(df_data)

    def _sum_dicts(self, data: list[dict]) -> list[int]:
        arr = [0]*12
        for dict_item, i in itertools.product(data, range(12)):
            val = dict_item.get(self.std_columns[i], 0)
            arr[i] += val or 0
        return arr

    def _calc_df(self) -> None:
        df = self._create_df()

        return (
            df
            .lazy()
            .with_columns(
                expenses_necessary=(
                    pl.lit(0)
                    + pl.col("expenses_necessary")
                    + pl.col("savings")
                    + pl.col("necessary")
                )
            )
            .with_columns(
                expenses_free=(pl.col("incomes") - pl.col("expenses_necessary"))
            )
            .with_columns(day_calced=(pl.col("expenses_free") / pl.col("month_len")))
            .with_columns(
                remains=(
                    pl.col("expenses_free")
                    - (pl.col("day_input") * pl.col("month_len"))
                )
            )
            .collect()
            .transpose(
                include_header=True, header_name="name", column_names=self.std_columns
            )
        )
