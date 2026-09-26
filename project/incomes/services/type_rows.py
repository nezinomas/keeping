from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from django.template.defaultfilters import floatformat

from ...core.lib.convert_price import int_cents_to_float
from ...core.lib.table_order import Column, TableOrder

NOTHING = "–"
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


def _amount(cents: int) -> str:
    return floatformat(int_cents_to_float(cents), "0g") if cents else NOTHING


def _share(cents: int, total: int) -> str:
    return f"{floatformat(cents / total * 100, '0')}%" if cents and total else NOTHING


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
        sums = {row["title"]: row["sum"] for row in year}
        last_sums = {row["title"]: row["sum"] for row in last_year}
        dates = {row["title"]: row["date"] for row in last_dates}
        total = sum(sums.values())

        rows = [
            _row(income_type, sums, last_sums, dates, total)
            for income_type in sorted(types, key=lambda t: t["title"])
        ]

        ordered = ORDER.sort(order, rows, lambda row: row.sort_values)
        return cls(
            rows=ordered.rows,
            total=TypeTotal(
                this_year=_amount(total),
                last_year=_amount(sum(last_sums.values())),
                share=_share(total, total),
            ),
            order=ordered.active,
        )


def _row(
    income_type: dict, sums: dict, last_sums: dict, dates: dict, total: int
) -> TypeRow:
    title = income_type["title"]
    this_year = sums.get(title, 0)
    last_year = last_sums.get(title, 0)
    # share runs with this year's sum; a figure the row has not got sorts last
    figures = {"this_year": this_year, "last_year": last_year, "share": this_year}
    sort_values = {
        "title": title,
        **{k: cents for k, cents in figures.items() if cents},
    }
    last_income = NOTHING
    if title in dates:
        sort_values["last_income"] = dates[title]
        last_income = f"{dates[title]:%Y-%m-%d}"

    return TypeRow(
        pk=income_type["id"],
        title=title,
        this_year=_amount(this_year),
        last_year=_amount(last_year),
        share=_share(this_year, total),
        last_income=last_income,
        sort_values=sort_values,
    )
