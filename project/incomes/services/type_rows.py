from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ...core.lib.money_cells import NOTHING, amount, day, share
from ...core.lib.table_order import Column, TableOrder

ORDER = TableOrder(
    columns=(
        Column("title"),
        Column("this_year", descending=True),
        Column("last_year", descending=True),
        Column("share", descending=True),
        Column("last_income", descending=True),
    ),
    default="title",
)


@dataclass(frozen=True)
class TypeRow:
    pk: int
    title: str
    this_year: str
    last_year: str
    share: str
    last_income: str
    sort_values: Mapping[str, Any]


@dataclass(frozen=True)
class TypeTotal:
    this_year: str
    last_year: str
    share: str


@dataclass(frozen=True)
class TypesTable:
    rows: list[TypeRow]
    total: TypeTotal
    order: str

    @classmethod
    def build(
        cls,
        types: Sequence[dict],
        year: Sequence[dict],
        last_year: Sequence[dict],
        last_dates: Sequence[dict],
        order: str,
    ) -> "TypesTable":
        sums = {row["pk"]: row["sum"] for row in year}
        last_sums = {row["pk"]: row["sum"] for row in last_year}
        dates = {row["pk"]: row["date"] for row in last_dates}
        total = sum(sums.values())

        rows = [
            _row(income_type, sums, last_sums, dates, total)
            for income_type in sorted(types, key=lambda t: t["title"])
        ]

        ordered = ORDER.sort(order, rows, lambda row: row.sort_values)
        return cls(
            rows=ordered.rows,
            total=TypeTotal(
                this_year=amount(total),
                last_year=amount(sum(last_sums.values())),
                share=share(total, total),
            ),
            order=ordered.active,
        )


def _row(
    income_type: dict, sums: dict, last_sums: dict, dates: dict, total: int
) -> TypeRow:
    pk = income_type["id"]
    title = income_type["title"]
    this_year = sums.get(pk, 0)
    last_year = last_sums.get(pk, 0)
    # share runs with this year's sum; a figure the row has not got sorts last
    figures = {"this_year": this_year, "last_year": last_year, "share": this_year}
    sort_values = {
        "title": title,
        **{k: cents for k, cents in figures.items() if cents},
    }
    last_income = NOTHING
    if pk in dates:
        sort_values["last_income"] = dates[pk]
        last_income = day(dates[pk])

    return TypeRow(
        pk=pk,
        title=title,
        this_year=amount(this_year),
        last_year=amount(last_year),
        share=share(this_year, total),
        last_income=last_income,
        sort_values=sort_values,
    )
