from collections import namedtuple
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

    def _sum(self, name: str, data) -> pl.Expr:
        data = data if isinstance(data, list) else list(data)

        def insert_missing_columns(df: DF) -> pl.Expr:
            diff = set(self.std_columns) - set(df.columns)
            return (
                df
                .with_columns([pl.lit(0).alias(col_name) for col_name in diff])
                .select(self.std_columns))

        return (
            pl.DataFrame(data)
            .lazy()
            .sum()
            .pipe(insert_missing_columns)
            .with_columns(pl.all().cast(pl.Int32))
            .with_columns(pl.lit(name).alias("name"))
            .collect()
        )

    def _create_df(self) -> DF:
        expenses_necessary, expenses_free = [], []
        for item in self._data.expenses:
            expenses_necessary.append(item) if item["necessary"] else expenses_free.append(item)

        rows = {
            "month_len": [
                {x: float(monthlen(self._year, x)) for x in self.std_columns}
            ],
            "incomes": self._data.incomes,
            "savings": self._data.savings,
            "day_input": self._data.days,
            "necessary": self._data.necessary,
            "expenses_necessary": expenses_necessary,
            "expenses_free": expenses_free,
        }
        list_of_df = [self._sum(k, v) for k, v in rows.items()]
        return pl.concat(list_of_df, how="vertical")

    def _calc_df(self) -> None:
        df = self._create_df().clone()

        df = (
            df
            .fill_null(0)
            .transpose(include_header=False, column_names=df["name"])
            .limit(12)
            .lazy()
            .with_columns(pl.all().cast(pl.Int32))
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
        return df
