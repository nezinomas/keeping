from collections.abc import Iterable
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ..lib.chart_view_model import ChartViewModel
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DrinkStats
from .consumption_year import ConsumptionYear


@dataclass(frozen=True)
class YearComparisonChartViewModel(ChartViewModel):
    title: str
    categories: list[str]
    serries: list[dict] = field(default_factory=list)
    unit: str = "ml"
    decimals: int = 0

    @property
    def has_data(self) -> bool:
        return bool(self.serries)


class YearComparison:
    """Average daily consumption of several years, plotted side by side.

    Owns both halves of the comparison: which years actually have records, and
    the chart the history tab draws from them. Years with no records drop out
    rather than showing as a flat line.
    """

    @classmethod
    def build(cls, user, years: Iterable[int]) -> YearComparisonChartViewModel:
        return cls._chart(user, cls._series(user, years))

    @classmethod
    def for_recent(cls, user, year: int, qty: int) -> YearComparisonChartViewModel:
        return cls.build(user, range(year - qty + 1, year + 1))

    @classmethod
    def for_pair(cls, user, year1, year2) -> YearComparisonChartViewModel:
        """All-or-nothing, unlike a span: half a comparison answers a question
        the user did not ask."""
        series = cls._series(user, [year1, year2])

        return cls._chart(user, series if len(series) == 2 else [])

    @classmethod
    def _chart(cls, user, series: list[dict]) -> YearComparisonChartViewModel:
        # every year is drawn in the unit the drink-type dropdown selects, so the
        # chart must be labelled with it rather than assuming millilitres
        converter = DrinkConverter(user.drink_type)

        return YearComparisonChartViewModel(
            title=_("Year comparison"),
            categories=list(month_names().values()),
            serries=series,
            unit=converter.display_unit,
            decimals=converter.display_decimals,
        )

    @staticmethod
    def _series(user, years: Iterable[int]) -> list[dict]:
        series = []

        for year in years:
            records = ConsumptionYear(user, int(year))
            if not records.monthly:
                continue

            stats = DrinkStats(records.converter, records.monthly)
            series.append({"name": year, "data": stats.monthly.avg_daily_volume})

        return series
