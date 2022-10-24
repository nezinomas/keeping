from dataclasses import dataclass, field
from datetime import date

from ...counts.lib.stats import Stats as CountStats
from ..managers import DrinkQuerySet


@dataclass
class CalendarChart:
    year: int
    data: DrinkQuerySet.sum_by_day
    latest_past_date: date = None

    chart_data: list[dict] = \
        field(init=False, default_factory=list)

    def __post_init__(self):
        if not self.data:
            return

        self.chart_data = \
            CountStats(
                year=self.year,
                data=self.data,
                past_latest=self.latest_past_date
            ).chart_calendar()
