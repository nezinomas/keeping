from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names

MONTHS = tuple(str(month) for month in range(1, 13))
ALL = "all"
OLD_ROUTE_ALL = "13"


@dataclass(frozen=True)
class FilterItem:
    label: str
    url: str
    active: bool


@dataclass(frozen=True)
class MonthFilter:
    value: str

    @classmethod
    def parse(cls, value: str, today: date) -> "MonthFilter":
        if value in (*MONTHS, ALL):
            return cls(value)
        if value == OLD_ROUTE_ALL:
            return cls(ALL)
        return cls(str(today.month))

    def items(self, tab_url: str) -> list[FilterItem]:
        labels = (*month_names().values(), _("All records"))
        return [
            FilterItem(label, f"{tab_url}?month={value}", value == self.value)
            for value, label in zip((*MONTHS, ALL), labels, strict=True)
        ]
