import calendar
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ...core.lib.year_boundary import YearBoundary
from ..lib.drinks_risk import HEAVY_DAY_STDAV
from .model_services import DrinkModelService

MONTHS = 12


@dataclass(frozen=True)
class MonthTotal:
    """One month of one year, as the pooled aggregate reads it out of the DB.

    Both halves are needed and neither implies the other: the Std Av says how
    much, the day count says over how many days of that month it was spread.
    """

    year: int
    month: int  # 1 = January
    stdav: float
    drinking_days: int


@dataclass(frozen=True)
class MonthPoint:
    """One month of the typical year, pooled over every year in the range.

    ``calendar_days`` is the denominator of the rate: how many days of that
    month the pooled years actually reached, so a January pooled over eleven
    years is divided by eleven Januaries and the year still running is only
    divided by the part of it that has happened.
    """

    month: int  # 1 = January
    calendar_days: int
    drinking_days: int
    stdav: float
    drinking_day_share: float  # drinking_days / calendar_days
    intensity: float  # stdav / drinking_days


@dataclass(frozen=True)
class TypicalYearProfile:
    """Twelve months pooled across a span of years, and which years those were.

    Pure: it takes the aggregated rows and a ``today``, so the pooling rule is
    testable without the ORM and the span it reports is read off the rows rather
    than assumed from the request.
    """

    points: list[MonthPoint]
    year_from: int = 0
    year_to: int = 0

    @property
    def has_data(self) -> bool:
        return bool(self.year_to)

    @classmethod
    def pool(
        cls, rows: Sequence[MonthTotal], today: date | None = None
    ) -> "TypicalYearProfile":
        """Sum each month across the years present, and each month's days with
        it.

        Only years that carry a Drink contribute days. A year the user never
        logged would otherwise add 365 dry days to every month of the profile,
        which reads as abstinence rather than as an absence of records.
        """
        years = sorted({row.year for row in rows})
        stdav = [0.0] * MONTHS
        drinking_days = [0] * MONTHS

        for row in rows:
            stdav[row.month - 1] += row.stdav
            drinking_days[row.month - 1] += row.drinking_days

        points = [
            cls._point(
                month=month,
                stdav=stdav[month - 1],
                drinking_days=drinking_days[month - 1],
                calendar_days=sum(
                    cls._days_reached(year, month, today) for year in years
                ),
            )
            for month in range(1, MONTHS + 1)
        ]

        return cls(
            points=points,
            year_from=years[0] if years else 0,
            year_to=years[-1] if years else 0,
        )

    @staticmethod
    def _days_reached(year: int, month: int, today: date | None) -> int:
        """How many days of one month of one year the calendar has reached.

        The year-boundary rule, read a month at a time: a finished year runs to
        Dec 31, the year still running only to today. Pooling the current year
        without this counts the months it has not lived through yet, and every
        rate after August comes out too low.
        """
        end = YearBoundary.for_year(year, today).end_date

        if month > end.month:
            return 0
        if month < end.month:
            return calendar.monthrange(year, month)[1]

        return end.day

    @staticmethod
    def _point(
        month: int, calendar_days: int, drinking_days: int, stdav: float
    ) -> MonthPoint:
        return MonthPoint(
            month=month,
            calendar_days=calendar_days,
            drinking_days=drinking_days,
            stdav=stdav,
            drinking_day_share=drinking_days / calendar_days if calendar_days else 0.0,
            intensity=stdav / drinking_days if drinking_days else 0.0,
        )


@dataclass(frozen=True)
class TypicalYearChartViewModel:
    categories: list[str]
    drinking_day_share: list[float]  # per cent of that month's days drunk on
    intensity: list[float]  # Std Av per Drinking day
    heavy_threshold: float
    year_from: int
    year_to: int
    text: dict[str, str]

    @property
    def has_data(self) -> bool:
        return bool(self.year_to)

    @property
    def as_dict(self) -> dict:
        return asdict(self)


class TypicalYear:
    """One typical year, pooled from as many of the user's years as they choose.

    The same object as the weekday profile, one period longer: a recurring
    shape, not a year-over-year level, which is why it belongs on Habits rather
    than History. Pooling is what makes the seasonal signal visible — eleven
    Julys say something no single July can.

    **No converter, deliberately.** The rate is a ratio and the intensity is a
    harm metric that stays in Std Av, so the drink-type dropdown reaches neither
    series. ``YearComparison`` on History *does* take a converter, and the
    asymmetry looks like an oversight until you notice the two charts plot
    different kinds of number.

    **Which years get pooled is the user's call.** A user whose early years hold
    one row per month would see that era wreck the profile, and the app has no
    multi-user-safe way to tell those years apart from sparse honest ones. So it
    does not try: the range is theirs to narrow, and the caption names whatever
    it ends up being.
    """

    @classmethod
    def build(
        cls, user, year_from: int | None = None, year_to: int | None = None
    ) -> TypicalYearChartViewModel:
        """The pooled chart for a range of years, or for every year on record.

        One query however many years are pooled: the aggregate groups in the DB
        and the pooling happens here, so a decade does not cost a query a year.
        """
        rows = [
            MonthTotal(**row)
            for row in DrinkModelService(user).sum_by_year_month(year_from, year_to)
        ]

        return TypicalYearBuilder(TypicalYearProfile.pool(rows)).chart()


class TypicalYearBuilder:
    def __init__(self, profile: TypicalYearProfile):
        self._profile = profile

    def chart(self) -> TypicalYearChartViewModel:
        points = self._profile.points

        return TypicalYearChartViewModel(
            categories=list(month_names().values()),
            drinking_day_share=[
                round(point.drinking_day_share * 100, 1) for point in points
            ],
            intensity=[round(point.intensity, 1) for point in points],
            heavy_threshold=HEAVY_DAY_STDAV,
            year_from=self._profile.year_from,
            year_to=self._profile.year_to,
            text={
                "title": _("Typical year"),
                "subtitle": self._caption(),
                "share": _("Drinking-day rate"),
                "share_unit": "%",
                "intensity": _("Per drinking day"),
                # Std Av, not display_unit: the plot line is the Heavy day
                # threshold, which is defined in Std Av, and a converted series
                # would leave it marking a level the columns no longer measure
                "intensity_unit": "Std Av",
                "threshold_label": _("Heavy day"),
            },
        )

    def _caption(self) -> str:
        """The years actually pooled, named on the chart.

        A narrowed range must never read as covering everything, so the caption
        states the span rather than leaving it to be inferred from the tab.
        """
        year_from, year_to = self._profile.year_from, self._profile.year_to

        if not self._profile.has_data:
            return ""

        if year_from == year_to:
            return str(year_to)

        return _("Pooled %(year_from)s–%(year_to)s") % {
            "year_from": year_from,
            "year_to": year_to,
        }
