from dataclasses import dataclass, field
from datetime import date, timedelta

from django.utils.translation import gettext as _

from ...core.lib.translation import weekday_names

DAYS = 5  # today and the four days before it


def _label(day: date, offset: int) -> str:
    if offset == 0:
        return _("Today")

    if offset == 1:
        return _("Yesterday")

    # weekday_names() is keyed Monday-first, the same order date.weekday() counts
    return list(weekday_names().values())[day.weekday()]


@dataclass
class RecentDaySelector:
    """The day picker in the quick-add sheet.

    Needs only a day — not a request, not a user — so it never follows the year
    a user happens to be browsing: a drink is logged on a real calendar day.
    """

    selected: str  # today as an ISO date, e.g. "1999-01-15"
    options: list[tuple[str, str]] = field(default_factory=list)  # (label, value)

    @classmethod
    def for_day(cls, today: date) -> "RecentDaySelector":
        days = [today - timedelta(days=offset) for offset in range(DAYS)]

        return cls(
            selected=days[0].isoformat(),
            # a list, not the enumerate it is built from: the template iterates
            # this after the dataclass is built
            options=[
                (_label(day, offset), day.isoformat())
                for offset, day in enumerate(days)
            ],
        )
