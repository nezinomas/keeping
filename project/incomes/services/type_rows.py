from collections.abc import Sequence
from dataclasses import dataclass

from django.template.defaultfilters import floatformat

from ...core.lib.convert_price import int_cents_to_float
from ..models import IncomeType

NOTHING = "–"
KIND_ORDER = {kind.value: index for index, kind in enumerate(IncomeType.Types)}


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
    starts_group: bool


@dataclass(frozen=True)
class TypeTotal:
    this_year: str
    last_year: str
    share: str


@dataclass(frozen=True)
class TypesTable:
    rows: list[TypeRow]
    total: TypeTotal

    @classmethod
    def build(
        cls,
        types: Sequence[dict],
        year: Sequence[dict],
        last_year: Sequence[dict],
        last_dates: Sequence[dict],
    ) -> "TypesTable":
        sums = {row["title"]: row["sum"] for row in year}
        last_sums = {row["title"]: row["sum"] for row in last_year}
        dates = {row["title"]: f"{row['date']:%Y-%m-%d}" for row in last_dates}
        total = sum(sums.values())

        ordered = sorted(
            types,
            key=lambda t: (KIND_ORDER.get(t["type"], len(KIND_ORDER)), t["title"]),
        )
        rows = []
        for index, income_type in enumerate(ordered):
            title = income_type["title"]
            rows.append(
                TypeRow(
                    pk=income_type["id"],
                    title=title,
                    this_year=_amount(sums.get(title, 0)),
                    last_year=_amount(last_sums.get(title, 0)),
                    share=_share(sums.get(title, 0), total),
                    last_income=dates.get(title, NOTHING),
                    starts_group=index > 0
                    and income_type["type"] != ordered[index - 1]["type"],
                )
            )

        return cls(
            rows=rows,
            total=TypeTotal(
                this_year=_amount(total),
                last_year=_amount(sum(last_sums.values())),
                share=_share(total, total),
            ),
        )
