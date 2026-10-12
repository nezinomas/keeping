from dataclasses import dataclass

from django.utils.translation import gettext as _

from ...core.lib import stat_card
from ...core.lib.stat_card import Card, EmptyStatCard, LevelStatCard
from ...core.lib.translation import weekday_names
from ..lib.drinks_frequency import FrequencyStats
from ..lib.drinks_risk import HEAVY_DAY_STDAV
from .consumption_year import ConsumptionYear
from .profile_chart import ProfileLayer, profile_chart_dict, profile_chart_text


@dataclass(frozen=True)
class WeekdayChartViewModel:
    categories: list[str]
    drinking_day_share: list[float]  # per cent of that weekday drunk on
    intensity: list[float]  # Std Av per Drinking day
    heavy_threshold: float
    text: dict[str, str]

    @property
    def layers(self) -> list[ProfileLayer]:
        """One span, and the tab already names it, so no label."""
        return [ProfileLayer(self.drinking_day_share, self.intensity)]

    @property
    def as_dict(self) -> dict:
        return profile_chart_dict(self)


class HabitsTab:
    """Recurring shape: which days a user drinks on, and how heavily when they do."""

    @classmethod
    def build(cls, user, year: int) -> dict:
        records = ConsumptionYear(user, year)

        stats = FrequencyStats(
            current_daily=records.daily,
            past_daily=records.previous.daily,
        )
        builder = HabitsBuilder(frequency_stats=stats)

        return {
            "chart_weekday": builder.chart_weekday(),
            "cards": builder.get_cards(),
        }


class HabitsBuilder:
    def __init__(self, frequency_stats: FrequencyStats):
        self._stats = frequency_stats

    def chart_weekday(self) -> WeekdayChartViewModel:
        layer = ProfileLayer.from_points(self._stats.weekday_profile())

        return WeekdayChartViewModel(
            # Monday-first, the order date.weekday() counts in
            categories=list(weekday_names().values()),
            drinking_day_share=layer.drinking_day_share,
            intensity=layer.intensity,
            heavy_threshold=HEAVY_DAY_STDAV,
            text=profile_chart_text(),
        )

    def get_cards(self) -> list[Card]:
        return [self._card_per_drinking_day()]

    def _card_per_drinking_day(self) -> Card:
        title = _("Per drinking day")
        intensity = self._stats.intensity

        if not intensity:
            return EmptyStatCard(title, _("No data"))

        # a harm metric stays in Std Av whatever the dropdown says - the Heavy
        # day threshold it is read against is defined there
        definition = _(
            "The year's Std Av divided by the days a Drink was recorded on, "
            "not by every day of the year."
        )
        unit_note = _(
            "Always in Std Av, because the Heavy day threshold is defined there."
        )

        return LevelStatCard(
            title,
            state=stat_card.HIGH if intensity > HEAVY_DAY_STDAV else stat_card.LOW,
            value=f"{intensity:.1f}",
            unit="Std Av",
            note=f"{_('Heavy day')}: > {HEAVY_DAY_STDAV:.0f} Std Av",
            explanation=(definition, unit_note),
        )
