from collections.abc import Sequence

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _


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
