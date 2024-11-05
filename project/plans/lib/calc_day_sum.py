from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from typing import Union

import polars as pl
from django.db.models import F
from django.utils.translation import gettext as _
from polars import DataFrame as DF

from ...core.lib.date import monthlen, monthname, monthnames
from ..models import DayPlan, ExpensePlan, IncomePlan, NecessaryPlan, SavingPlan


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
            title=F("expense_type__title"),
        )

        self.savings = SavingPlan.objects.year(self.year).values(*month_names)
        self.days = DayPlan.objects.year(self.year).values(*month_names)
        self.necessary = (
            NecessaryPlan.objects.year(self.year)
            .values(*month_names)
            .annotate(title=F("expense_type__title"))
        )


class PlanCalculateDaySum:
    def __init__(self, data: PlanCollectData):
        self.std_columns = monthnames()

        self._data = data
        self._year = data.year
        self._df = self._calc_df()

    def filter_df(self, name: str) -> DF:
        if name not in self._df["name"]:
            return {}

        data = self._df.filter(pl.col("name") == name)
        return self._return_data(data)

    @property
    def plans_stats(self):
        Items = namedtuple("Items", ["type", *self.std_columns])

        _incomes = _("Incomes")
        _median = _("median")
        _necessary = _("Necessary expenses")
        _remain = _("Remains for everyday")
        _full = _("Full expenses")
        _residual = _("Residual")
        _sum_per_day = _("Sum per day")
        _days = _("days in month")
        _from_tables = _("from tables above")

        return [
            Items(
                type=f"1. {_incomes} ({_median})",
                **self.filter_df("incomes_avg")
            ),
            Items(
                type=f"2. {_necessary}",
                **self.filter_df("expenses_necessary")
            ),
            Items(
                type=f"3. {_remain} (1 - 2)",
                **self.filter_df("expenses_free")
            ),
            Items(
                type=f"4. {_remain} ({_from_tables})",
                **self.filter_df("expenses_free2"),
            ),
            Items(
                type=f"5. {_full} (1 + 4)",
                **self.filter_df("expenses_full")
            ),
            Items(
                type=f"6. {_incomes} - {_full} (1 - 5)",
                **self.filter_df("expenses_remains"),
            ),
            Items(
                type=f"7. {_sum_per_day} (3 / {_days})",
                **self.filter_df("day_calced")
            ),
            Items(
                type=f"8. {_residual} (3 - 7 * {_days})",
                **self.filter_df("remains")
            ),
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
            "expenses_free2": self._sum_dicts(list(expenses_free)),
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
            .with_columns(incomes_avg=pl.col.incomes.median())
            .with_columns(
                expenses_necessary=(
                    pl.lit(0)
                    + pl.col("expenses_necessary")
                    + pl.col("savings")
                    + pl.col("necessary")
                )
            )
            .with_columns(
                expenses_free=(pl.col.incomes_avg - pl.col.expenses_necessary)
            )
            .with_columns(
                expenses_full=(pl.col("expenses_necessary") + pl.col("expenses_free2"))
            )
            .with_columns(day_calced=(pl.col("expenses_free") / pl.col("month_len")))
            .with_columns(
                remains=(
                    pl.col("expenses_free")
                    - (pl.col("day_input") * pl.col("month_len"))
                )
            )
            .with_columns(expenses_remains=(pl.col.incomes_avg - pl.col.expenses_full))
            .collect()
            .transpose(
                include_header=True, header_name="name", column_names=self.std_columns
            )
        )
