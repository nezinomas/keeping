from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from ...core.lib.collation import lt_title
from ...core.lib.type_table import Cells, Figures, Total, TypeOrder, figures_by_pk
from ...core.lib.year_boundary import YearBoundary
from ...users.models import User
from .model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
    ExpenseTypeModelService,
)

ORDER = TypeOrder(last_key="last_expense")


@dataclass(frozen=True)
class NameRow(Cells):
    year: str


@dataclass(frozen=True)
class TypeRow(Cells):
    names: list[NameRow]
    necessary: bool


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
        figures = figures_by_pk([n["id"] for n in names], year, last_year, last_dates)
        grand = Figures.summed(list(figures.values()))
        by_type = _names_by_type(names)
        rows = [
            _type_row(type_, by_type[type_["id"]], figures, grand.this_year, order)
            for type_ in sorted(types, key=lambda t: lt_title(t["title"]))
        ]

        ordered = ORDER.sort(order, rows)
        return cls(rows=ordered.rows, total=Total.of(grand), order=ordered.active)


def _names_by_type(names: Sequence[dict]) -> dict[int, list[dict]]:
    by_type = defaultdict(list)
    # by title first, so names tied on a sorted figure keep the alphabet
    for name in sorted(names, key=lambda n: lt_title(n["title"])):
        by_type[name["parent_id"]].append(name)
    return by_type


def _type_row(
    type_: dict, group: list[dict], figures: dict[int, Figures], grand: int, order: str
) -> TypeRow:
    type_figures = Figures.summed([figures[n["id"]] for n in group])
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
    return ORDER.sort(order, listed).rows


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
