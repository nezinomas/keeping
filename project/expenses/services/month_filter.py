from dataclasses import dataclass
from datetime import date

from django.urls import reverse
from django.utils.translation import gettext as _

from ...core.lib.translation import month_names

MONTHS = tuple(str(month) for month in range(1, 13))
ALL = "all"


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
        return cls.at(today)

    @classmethod
    def at(cls, day: date) -> "MonthFilter":
        return cls(str(day.month))

    def url(self) -> str:
        return reverse("expenses:tab_data", args=[self.value])

    def lookup(self) -> dict:
        if self.value == ALL:
            return {}
        return {"date__month": int(self.value)}

    def items(self) -> list[FilterItem]:
        labels = (*month_names().values(), _("All records"))
        return [
            FilterItem(label, MonthFilter(value).url(), value == self.value)
            for value, label in zip((*MONTHS, ALL), labels, strict=True)
        ]
