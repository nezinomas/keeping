from collections.abc import Sequence
from dataclasses import dataclass

from ...core.lib.collation import lt_title
from ...core.lib.type_table import Cells, Figures, Total, TypeOrder, figures_by_pk
from ...core.lib.year_boundary import YearBoundary
from ...users.models import User
from .model_services import IncomeModelService, IncomeTypeModelService

ORDER = TypeOrder(last_key="last_income")


@dataclass(frozen=True)
class TypesTable:
    rows: list[Cells]
    total: Total
    order: str

    @classmethod
    def read(cls, user: User, boundary: YearBoundary, order: str) -> "TypesTable":
        incomes = IncomeModelService(user)
        types = IncomeTypeModelService(user).items().values("id", "title")
        return cls.build(
            types=list(types),
            year=list(incomes.sum_by_between("income_type", *boundary.span)),
            last_year=list(
                incomes.sum_by_between("income_type", *boundary.previous_span)
            ),
            last_dates=list(incomes.last_date_by("income_type", boundary.end_date)),
            order=order,
        )

    @classmethod
    def build(
        cls,
        types: Sequence[dict],
        year: Sequence[dict],
        last_year: Sequence[dict],
        last_dates: Sequence[dict],
        order: str,
    ) -> "TypesTable":
        figures = figures_by_pk([t["id"] for t in types], year, last_year, last_dates)
        grand = Figures.summed(list(figures.values()))
        rows = [
            Cells(
                pk=income_type["id"],
                title=income_type["title"],
                title_key=lt_title(income_type["title"]),
                figures=figures[income_type["id"]],
                share_of=grand.this_year,
            )
            for income_type in sorted(types, key=lambda t: lt_title(t["title"]))
        ]

        ordered = ORDER.sort(order, rows)
        return cls(rows=ordered.rows, total=Total.of(grand), order=ordered.active)
