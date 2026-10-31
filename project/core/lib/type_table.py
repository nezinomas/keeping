from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cached_property
from typing import Any

from .money_cells import NOTHING, amount, day, share
from .table_order import Column, Ordered, TableOrder


@dataclass(frozen=True)
class Figures:
    this_year: int
    last_year: int
    dates: list[date]

    @classmethod
    def summed(cls, figures: Sequence["Figures"]) -> "Figures":
        return cls(
            this_year=sum(f.this_year for f in figures),
            last_year=sum(f.last_year for f in figures),
            dates=[d for f in figures for d in f.dates],
        )

    @property
    def latest(self) -> date:
        return max(self.dates)


def figures_by_pk(
    pks: Sequence[int],
    year: Sequence[dict],
    last_year: Sequence[dict],
    last_dates: Sequence[dict],
) -> dict[int, Figures]:
    sums = {row["pk"]: row["sum"] for row in year}
    last_sums = {row["pk"]: row["sum"] for row in last_year}
    dates = {row["pk"]: row["date"] for row in last_dates}
    return {
        pk: Figures(
            this_year=sums.get(pk, 0),
            last_year=last_sums.get(pk, 0),
            dates=[dates[pk]] if pk in dates else [],
        )
        for pk in pks
    }


@dataclass(frozen=True)
class Cells:
    pk: int
    title: str
    title_key: tuple
    figures: Figures
    share_of: int

    @property
    def this_year(self) -> str:
        return amount(self.figures.this_year)

    @property
    def last_year(self) -> str:
        return amount(self.figures.last_year)

    @property
    def share(self) -> str:
        return share(self.figures.this_year, self.share_of)

    @property
    def last_date(self) -> str:
        if not self.figures.dates:
            return NOTHING
        return day(self.figures.latest)


@dataclass(frozen=True)
class Total:
    this_year: str
    last_year: str
    share: str

    @classmethod
    def of(cls, figures: Figures) -> "Total":
        return cls(
            this_year=amount(figures.this_year),
            last_year=amount(figures.last_year),
            share=share(figures.this_year, figures.this_year),
        )


@dataclass(frozen=True)
class TypeOrder:
    last_key: str

    @cached_property
    def _columns(self) -> TableOrder:
        return TableOrder(
            columns=(
                Column("title"),
                Column("this_year", descending=True),
                Column("last_year", descending=True),
                Column("share", descending=True),
                Column(self.last_key, descending=True),
            ),
            default="title",
        )

    def sort[T: Cells](self, order: str, rows: Sequence[T]) -> Ordered[T]:
        return self._columns.sort(order, rows, self._values)

    def _values(self, row: Cells) -> Mapping[str, Any]:
        # share runs with this year's sum; a figure the row has not got sorts last
        sums = {
            "this_year": row.figures.this_year,
            "last_year": row.figures.last_year,
            "share": row.figures.this_year,
        }
        values = {
            "title": row.title_key,
            **{k: cents for k, cents in sums.items() if cents},
        }
        if row.figures.dates:
            values[self.last_key] = row.figures.latest
        return values
