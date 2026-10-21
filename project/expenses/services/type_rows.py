from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from ...core.lib.collation import lt_title
from ...core.lib.money_cells import NOTHING, amount, share
from ...core.lib.table_order import Column, TableOrder

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
class NameRow:
    pk: int
    title: str
    this_year: str
    last_year: str
    share: str
    last_expense: str
    sort_values: Mapping[str, Any]
    year: str


@dataclass(frozen=True)
class TypeRow:
    pk: int
    title: str
    this_year: str
    last_year: str
    share: str
    last_expense: str
    sort_values: Mapping[str, Any]
    names: list[NameRow]


@dataclass(frozen=True)
class Total:
    this_year: str
    last_year: str
    share: str


@dataclass(frozen=True)
class _Figures:
    this_year: int
    last_year: int
    dates: list[date]


@dataclass(frozen=True)
class GroupedTypesTable:
    rows: list[TypeRow]
    total: Total
    order: str

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
        sums = {row["pk"]: row["sum"] for row in year}
        last_sums = {row["pk"]: row["sum"] for row in last_year}
        dates = {row["pk"]: row["date"] for row in last_dates}

        by_type = defaultdict(list)
        for name in sorted(names, key=lambda n: lt_title(n["title"])):
            by_type[name["parent_id"]].append(name)

        figures = {
            name["id"]: _Figures(
                this_year=sums.get(name["id"], 0),
                last_year=last_sums.get(name["id"], 0),
                dates=[dates[name["id"]]] if name["id"] in dates else [],
            )
            for name in names
        }
        total = sum(f.this_year for f in figures.values())

        rows = []
        for type_ in sorted(types, key=lambda t: lt_title(t["title"])):
            group = by_type[type_["id"]]
            type_figures = _Figures(
                this_year=sum(figures[n["id"]].this_year for n in group),
                last_year=sum(figures[n["id"]].last_year for n in group),
                dates=[d for n in group for d in figures[n["id"]].dates],
            )
            listed = [
                _name_row(n, figures[n["id"]], type_figures.this_year) for n in group
            ]
            rows.append(
                TypeRow(
                    names=ORDER.sort(order, listed, lambda r: r.sort_values).rows,
                    **_cells(
                        type_["id"],
                        type_["title"],
                        lt_title(type_["title"]),
                        type_figures,
                        total,
                    ),
                )
            )

        ordered = ORDER.sort(order, rows, lambda row: row.sort_values)
        return cls(
            rows=ordered.rows,
            total=Total(
                this_year=amount(total),
                last_year=amount(sum(f.last_year for f in figures.values())),
                share=share(total, total),
            ),
            order=ordered.active,
        )


def _limit(name: dict) -> str:
    """The year a name is limited to, "" when it is not; its NULL ends here."""
    return str(name["valid_for"]) if name["valid_for"] else ""


def _title_key(limit: str, title: str) -> tuple:
    if not limit:
        return (0, 0, lt_title(title))
    return (1, -int(limit), lt_title(title))


def _name_row(name: dict, figures: _Figures, type_total: int) -> NameRow:
    limit = _limit(name)
    return NameRow(
        year=limit,
        **_cells(
            name["id"],
            name["title"],
            _title_key(limit, name["title"]),
            figures,
            type_total,
        ),
    )


def _cells(
    pk: int, title: str, title_key: tuple, figures: _Figures, whole: int
) -> dict:
    # share runs with this year's sum; a figure the row has not got sorts last
    sums = {
        "this_year": figures.this_year,
        "last_year": figures.last_year,
        "share": figures.this_year,
    }
    sort_values = {
        "title": title_key,
        **{k: cents for k, cents in sums.items() if cents},
    }
    last_expense = NOTHING
    if figures.dates:
        latest = max(figures.dates)
        sort_values["last_expense"] = latest
        last_expense = f"{latest:%Y-%m-%d}"

    return {
        "pk": pk,
        "title": title,
        "this_year": amount(figures.this_year),
        "last_year": amount(figures.last_year),
        "share": share(figures.this_year, whole),
        "last_expense": last_expense,
        "sort_values": sort_values,
    }
