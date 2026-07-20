from dataclasses import asdict, dataclass

from django.utils.translation import gettext as _

from ...lib.drinks_trend import ProjectionStats, SlopeStats, TrendStats, YtdStats


@dataclass(frozen=True)
class TrendChartViewModel:
    categories: list[str]
    rolling_7: list[float]
    rolling_30: list[float]
    target: float | None
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        """Bridges the gap between strict DTOs and Django's json_script"""
        return asdict(self)


class TrendsBuilder:
    def __init__(self, drink_stats: TrendStats, target: float = 0.0):
        self._stats = drink_stats
        self._target = target

    def chart_trend(self) -> TrendChartViewModel:
        return TrendChartViewModel(
            categories=self._stats.categories,
            rolling_7=[round(v) for v in self._stats.rolling(7)],
            rolling_30=[round(v) for v in self._stats.rolling(30)],
            target=self._target or None,
            text={
                "r7": _("7-day average"),
                "r30": _("30-day average"),
                "limit": _("Limit"),
                "ml": _("Daily consumption, milliliters"),
            },
        )

    def trend_slope(self) -> SlopeStats:
        return self._stats.slope()

    def trend_ytd(self) -> YtdStats:
        return self._stats.ytd()

    def trend_projection(self) -> ProjectionStats:
        return self._stats.projection()
