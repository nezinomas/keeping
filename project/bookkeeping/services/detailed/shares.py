from collections.abc import Sequence

from django.utils.translation import gettext as _

from ....core.lib.money_cells import share


def _year_total(tables: Sequence[dict]) -> int:
    return sum(table["total"]["total_col"] for table in tables)


def with_subtitles(tables: Sequence[dict]) -> list[dict]:
    year_total = _year_total(tables)

    return [
        table
        | {
            "subtitle": _("%(share)s of the year's total")
            % {"share": share(table["total"]["total_col"], year_total)}
        }
        for table in tables
    ]
