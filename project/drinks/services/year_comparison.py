from collections.abc import Iterable
from dataclasses import asdict, dataclass, field

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ..lib.drinks_stats import DrinkStats
from .consumption_year import ConsumptionYear


@dataclass(frozen=True)
class YearComparisonChartViewModel:
    title: str
    categories: list[str]
    serries: list[dict] = field(default_factory=list)

    @property
    def has_data(self) -> bool:
        return bool(self.serries)

    @property
    def as_dict(self) -> dict:
        return asdict(self)


class YearComparison:
    """Average daily consumption of several years, plotted side by side.

    Owns both halves of the comparison: which years actually have records, and
    the chart the history tab draws from them. Years with no records drop out
    rather than showing as a flat line.
    """

    @classmethod
    def build(cls, user, years: Iterable[int]) -> YearComparisonChartViewModel:
        return YearComparisonChartViewModel(
            title=_("Year comparison"),
            categories=list(month_names().values()),
            serries=cls._series(user, years),
        )

    @staticmethod
    def _series(user, years: Iterable[int]) -> list[dict]:
        series = []

        for year in years:
            records = ConsumptionYear(user, int(year))
            if not records.monthly:
                continue

            stats = DrinkStats(records.converter, records.monthly)
            series.append({"name": year, "data": stats.monthly.avg_daily_volume_ml})

        return series
