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

    def url(self, tab_url: str) -> str:
        return f"{tab_url}?month={self.value}"

    def lookup(self) -> dict:
        if self.value == ALL:
            return {}
        return {"date__month": int(self.value)}

    def items(self, tab_url: str) -> list[FilterItem]:
        labels = (*month_names().values(), _("All records"))
        return [
            FilterItem(label, MonthFilter(value).url(tab_url), value == self.value)
            for value, label in zip((*MONTHS, ALL), labels, strict=True)
        ]
