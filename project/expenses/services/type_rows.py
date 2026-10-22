from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cached_property
from typing import Any

from ...core.lib.collation import lt_title
from ...core.lib.money_cells import NOTHING, amount, day, share
from ...core.lib.table_order import Column, TableOrder
from ...core.lib.year_boundary import YearBoundary
from ...users.models import User
from .model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
    ExpenseTypeModelService,
)

ORDER = TableOrder(
    columns=(
        Column("title"),
        Column("this_year", descending=True),
        Column("last_year", descending=True),
        Column("share", descending=True),
        Column("last_expense", descending=True),
    ),
    default="title",
)


@dataclass(frozen=True)
class Figures:
    this_year: int
    last_year: int
    dates: list[date]


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
    def last_expense(self) -> str:
        if not self.figures.dates:
            return NOTHING
        return day(max(self.figures.dates))

    @cached_property
    def sort_values(self) -> Mapping[str, Any]:
        # share runs with this year's sum; a figure the row has not got sorts last
        sums = {
            "this_year": self.figures.this_year,
            "last_year": self.figures.last_year,
            "share": self.figures.this_year,
        }
        values = {
            "title": self.title_key,
            **{k: cents for k, cents in sums.items() if cents},
        }
        if self.figures.dates:
            values["last_expense"] = max(self.figures.dates)
        return values


@dataclass(frozen=True)
class NameRow(Cells):
    year: str


@dataclass(frozen=True)
class TypeRow(Cells):
    names: list[NameRow]
    necessary: bool


@dataclass(frozen=True)
class Total:
    this_year: str
    last_year: str
    share: str


@dataclass(frozen=True)
class GroupedTypesTable:
    rows: list[TypeRow]
    total: Total
    order: str

    @classmethod
    def read(
        cls, user: User, boundary: YearBoundary, order: str
    ) -> "GroupedTypesTable":
        expenses = ExpenseModelService(user)
        types = ExpenseTypeModelService(user).items().values("id", "title", "necessary")
        names = (
            ExpenseNameModelService(user)
            .items()
            .values("id", "title", "parent_id", "valid_for")
        )
        return cls.build(
            types=list(types),
            names=list(names),
            year=list(expenses.sum_by_between("expense_name", *boundary.span)),
            last_year=list(
                expenses.sum_by_between("expense_name", *boundary.previous_span)
            ),
            last_dates=list(expenses.last_date_by("expense_name", boundary.end_date)),
            order=order,
        )

    @classmethod
    def build(
        cls,
        types: Sequence[dict],
        names: Sequence[dict],
        year: Sequence[dict],
        last_year: Sequence[dict],
        last_dates: Sequence[dict],
        order: str,
    ) -> "GroupedTypesTable":
        figures = _name_figures(names, year, last_year, last_dates)
        grand = _summed(list(figures.values()))
        by_type = _names_by_type(names)
        rows = [
            _type_row(type_, by_type[type_["id"]], figures, grand.this_year, order)
            for type_ in sorted(types, key=lambda t: lt_title(t["title"]))
        ]

        ordered = ORDER.sort(order, rows, lambda row: row.sort_values)
        return cls(rows=ordered.rows, total=_total(grand), order=ordered.active)


def _name_figures(
    names: Sequence[dict],
    year: Sequence[dict],
    last_year: Sequence[dict],
    last_dates: Sequence[dict],
) -> dict[int, Figures]:
    sums = {row["pk"]: row["sum"] for row in year}
    last_sums = {row["pk"]: row["sum"] for row in last_year}
    dates = {row["pk"]: row["date"] for row in last_dates}
    return {
        name["id"]: Figures(
            this_year=sums.get(name["id"], 0),
            last_year=last_sums.get(name["id"], 0),
            dates=[dates[name["id"]]] if name["id"] in dates else [],
        )
        for name in names
    }


def _summed(figures: Sequence[Figures]) -> Figures:
    return Figures(
        this_year=sum(f.this_year for f in figures),
        last_year=sum(f.last_year for f in figures),
        dates=[d for f in figures for d in f.dates],
    )


def _names_by_type(names: Sequence[dict]) -> dict[int, list[dict]]:
    by_type = defaultdict(list)
    # by title first, so names tied on a sorted figure keep the alphabet
    for name in sorted(names, key=lambda n: lt_title(n["title"])):
        by_type[name["parent_id"]].append(name)
    return by_type


def _type_row(
    type_: dict, group: list[dict], figures: dict[int, Figures], grand: int, order: str
) -> TypeRow:
    type_figures = _summed([figures[n["id"]] for n in group])
    return TypeRow(
        pk=type_["id"],
        title=type_["title"],
        title_key=lt_title(type_["title"]),
        figures=type_figures,
        share_of=grand,
        names=_name_rows(group, figures, type_figures.this_year, order),
        necessary=type_["necessary"],
    )


def _name_rows(
    group: list[dict], figures: dict[int, Figures], type_total: int, order: str
) -> list[NameRow]:
    listed = [_name_row(n, figures[n["id"]], type_total) for n in group]
    return ORDER.sort(order, listed, lambda row: row.sort_values).rows


def _total(grand: Figures) -> Total:
    return Total(
        this_year=amount(grand.this_year),
        last_year=amount(grand.last_year),
        share=share(grand.this_year, grand.this_year),
    )


def _limit(name: dict) -> str:
    """The year a name is limited to, "" when it is not; its NULL ends here."""
    return str(name["valid_for"]) if name["valid_for"] else ""


def _title_key(limit: str, title: str) -> tuple:
    if not limit:
        return (0, 0, lt_title(title))
    return (1, -int(limit), lt_title(title))


def _name_row(name: dict, figures: Figures, type_total: int) -> NameRow:
    limit = _limit(name)
    return NameRow(
        pk=name["id"],
        title=name["title"],
        title_key=_title_key(limit, name["title"]),
        figures=figures,
        share_of=type_total,
        year=limit,
    )
