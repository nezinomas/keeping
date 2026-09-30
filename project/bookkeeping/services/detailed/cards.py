from collections.abc import Sequence
from dataclasses import dataclass

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _

from ....core.lib.convert_price import int_cents_to_float
from ....core.lib.stat_card import Card, StatCard


def _euro(cents: int) -> str:
    return floatformat(int_cents_to_float(cents), "0g")


def _year_total(tables: Sequence[dict]) -> int:
    return sum(table["total"]["total_col"] for table in tables)


def _share(cents: int, year_total: int) -> str:
    if not year_total:
        return "0"

    percent = cents / year_total * 100

    return "< 1" if percent < 0.5 else floatformat(percent, "0")


def with_subtitles(tables: Sequence[dict]) -> list[dict]:
    year_total = _year_total(tables)

    return [
        table
        | {
            "subtitle": _("%(share)s%% of the year's total")
            % {"share": _share(table["total"]["total_col"], year_total)}
        }
        for table in tables
    ]


@dataclass(frozen=True)
class ExpenseCards:
    tables: Sequence[dict]

    @classmethod
    def build(cls, tables: Sequence[dict]) -> list[Card]:
        if not tables:
            return []

        return cls(tables)._cards()

    def _cards(self) -> list[Card]:
        year_total = _year_total(self.tables)

        return [
            self._largest_type(year_total),
            self._largest_expense(year_total),
        ]

    def _largest_type(self, year_total: int) -> Card:
        largest = max(self.tables, key=lambda table: table["total"]["total_col"])
        cents = largest["total"]["total_col"]

        return StatCard(
            title=_("Largest type"),
            value=largest["title"],
            note=_("%(amount)s € · %(share)s%% of the year's total")
            % {"amount": _euro(cents), "share": _share(cents, year_total)},
            explanation=(
                _("The expense type with the biggest share of this year's expenses"),
            ),
        )

    def _largest_expense(self, year_total: int) -> Card:
        # sorted by name so a re-sorted table cannot change which tie wins
        expense_type, row = max(
            (
                (table["title"], row)
                for table in self.tables
                for row in sorted(table["data"], key=lambda row: row["title"])
            ),
            key=lambda pair: pair[1]["total_col"],
        )
        cents = row["total_col"]

        return StatCard(
            title=_("Largest expense"),
            value=row["title"],
            note=_("%(amount)s € · %(share)s%% · %(type)s")
            % {
                "amount": _euro(cents),
                "share": _share(cents, year_total),
                "type": expense_type,
            },
            explanation=(
                _(
                    "The expense with the biggest share of this year's expenses, "
                    "across all types"
                ),
            ),
        )
