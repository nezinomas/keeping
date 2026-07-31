from dataclasses import asdict, dataclass

from django.utils.translation import gettext as _

from ...core.lib.translation import weekday_names
from ..lib.drinks_frequency import FrequencyStats
from ..lib.drinks_risk import HEAVY_DAY_STDAV
from . import stat_card
from .consumption_year import ConsumptionYear
from .stat_card import StatCard


@dataclass(frozen=True)
class WeekdayChartViewModel:
    categories: list[str]
    drinking_day_share: list[float]  # per cent of that weekday drunk on
    intensity: list[float]  # Std Av per Drinking day
    heavy_threshold: float
    text: dict[str, str]

    @property
    def as_dict(self) -> dict:
        return asdict(self)


class HabitsTab:
    """Deep module for recurring shape — as opposed to level (Overview),
    direction (Trends) or harm (Risk).

    Which days a user drinks on, and how heavily when they do: two independent
    behaviours that every year-wide average fuses back together. The tab reads
    one year, the one the header selects, like every other tab.
    """

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
        profile = self._stats.weekday_profile()

        return WeekdayChartViewModel(
            # weekday_names() is keyed Monday-first, the same order
            # date.weekday() counts in and weekday_profile() returns
            categories=list(weekday_names().values()),
            drinking_day_share=[
                round(point.drinking_day_share * 100, 1) for point in profile
            ],
            intensity=[round(point.intensity, 1) for point in profile],
            heavy_threshold=HEAVY_DAY_STDAV,
            text={
                "title": _("Weekday profile"),
                "share": _("Drinking-day rate"),
                "share_unit": "%",
                "intensity": _("Per drinking day"),
                # deliberately not display_unit: the intensity axis carries a
                # plot line at HEAVY_DAY_STDAV, which is defined in Std Av, so
                # converting the series with the drink-type dropdown would leave
                # the line marking a level the columns no longer measure
                "intensity_unit": "Std Av",
                "threshold_label": _("Heavy day"),
            },
        )

    def get_cards(self) -> list[StatCard]:
        return [self._card_per_drinking_day()]

    def _card_per_drinking_day(self) -> StatCard:
        title = _("Per drinking day")
        intensity = self._stats.intensity

        if not intensity:
            return StatCard.empty(title, _("No data"))

        # Intensity is a harm metric, so it stays in Std Av whatever the drink
        # type dropdown says: the Heavy day threshold it is read against is
        # defined there, and one decimal is what a Std Av needs to survive.
        definition = _(
            "The year's Std Av divided by the days a Drink was recorded on, "
            "not by every day of the year."
        )
        unit_note = _(
            "Always in Std Av, because the Heavy day threshold is defined there."
        )

        return StatCard.level(
            title,
            state=stat_card.HIGH if intensity > HEAVY_DAY_STDAV else stat_card.LOW,
            value=f"{intensity:.1f} Std Av",
            note=f"{_('Heavy day')}: > {HEAVY_DAY_STDAV:.0f} Std Av",
            explanation=f"{definition} {unit_note}",
        )
