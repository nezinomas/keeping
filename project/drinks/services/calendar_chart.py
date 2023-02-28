from dataclasses import dataclass, field
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.translation import weekday_names
from ...counts.lib.stats import Stats as CountStats
from ..managers import DrinkQuerySet


@dataclass
class CalendarChart:
    year: int
    data: DrinkQuerySet.sum_by_day
    latest_past_date: date = None

    chart_data: CountStats.chart_calendar = field(init=False, default_factory=list)

    def __post_init__(self):
        if not self.data:
            return

        self.chart_data = CountStats(
            year=self.year, data=self.data, past_latest=self.latest_past_date
        ).chart_calendar()

    def full_calendar(self, data: list[dict]) -> dict:
        return {
            "data": data,
            "categories": [x[0] for x in list(weekday_names().values())],
            "text": {
                "gap": _("Gap"),
                "quantity": _("Quantity"),
            },
        }

    def first_half_of_year(self):
        return self.full_calendar(self.chart_data[:6])

    def second_half_of_year(self):
        return self.full_calendar(self.chart_data[6:])
