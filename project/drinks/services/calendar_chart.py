from dataclasses import dataclass, field
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.translation import weekday_names
from ...counts.lib.stats import Calendar
from ...counts.lib.stats import Stats as CountStats
from ..lib.drinks_options import DrinkConverter
from ..services.model_services import DrinkModelService


@dataclass
class CalendarChart:
    year: int
    drink_type: str
    daily_data: DrinkModelService.sum_by_day
    latest_past_date: date = None

    chart_data: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.converter = DrinkConverter(self.drink_type)

        if not self.daily_data:
            return

        stats = CountStats(
            year=self.year, data=self.daily_data, past_latest=self.latest_past_date
        )
        self.chart_data = Calendar(stats).chart_data()

    def full_calendar(self, data: list[dict]) -> dict:
        return {
            "data": data,
            "categories": [name[0] for name in list(weekday_names().values())],
            "ratio": self.converter.stdav_per_unit,
            "text": {
                "gap": _("Gap"),
                "quantity": _("Quantity"),
            },
        }

    def first_half_of_year(self):
        return self.full_calendar(data=self.chart_data[:6])

    def second_half_of_year(self):
        return self.full_calendar(data=self.chart_data[6:])
