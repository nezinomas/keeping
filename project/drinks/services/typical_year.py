import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ...core.lib.year_boundary import YearBoundary
from ..lib.drinks_risk import HEAVY_DAY_STDAV
from .model_services import DrinkModelService
from .profile_chart import ProfileLayer, profile_chart_dict

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
class PooledRange:
    """The years a pooled layer is drawn from — the user's explicit ask.

    Open-ended by default: zeros mean every year on record, which is what the
    All-years preset asks for. Narrowing it is what keeps a month-per-row era
    out of the profile without the app deciding whose years to trust.
    """

    year_from: int = 0
    year_to: int = 0

    @classmethod
    def resolve(cls, year: int, qty: int | None = None) -> "PooledRange":
        if qty is None:
            return NoPooledRange()

        if not qty:
            return cls()

        return cls(year - qty + 1, year)

    def profile(self, service: DrinkModelService) -> TypicalYearProfile:
        """One query however many years are pooled: the aggregate groups in the
        DB and the pooling happens here, so a decade does not cost a query a
        year."""
        rows = [
            MonthTotal(**row)
            for row in service.sum_by_year_month(self.year_from, self.year_to)
        ]

        return TypicalYearProfile.pool(rows)


class NoPooledRange(PooledRange):
    """Nothing pooled: the chart opens on the header year alone.

    A state of its own rather than a None, so no caller branches on whether a
    range was asked for — this answers the same question with an empty profile,
    and costs no query doing it. The chart stays this way until the user presses
    a preset or Filter, because pooling a decade behind the year they are
    looking at is a reading to ask for, not one to be given unasked.
    """

    def profile(self, service: DrinkModelService) -> TypicalYearProfile:
        return TypicalYearProfile.pool([])


@dataclass(frozen=True)
class TypicalYearChartViewModel:
    categories: list[str]
    year: ProfileLayer  # the header year, always drawn, always in front
    pooled: ProfileLayer  # the range the user asked to pool, behind it
    heavy_threshold: float
    text: dict[str, str]
    # the span actually pooled, for the range boxes — not plotted, so `as_dict`
    # leaves it out
    year_from: int = 0
    year_to: int = 0

    @property
    def has_data(self) -> bool:
        return bool(self.layers)

    @property
    def layers(self) -> list[ProfileLayer]:
        """Back to front: the pooled range is the backdrop the header year is
        read against, so it is drawn first and the year sits on top of it."""
        return [layer for layer in (self.pooled, self.year) if layer.has_data]

    @property
    def as_dict(self) -> dict:
        return profile_chart_dict(self)


class TypicalYear:
    """One typical year, pooled from as many of the user's years as they choose,
    behind the year they are looking at.

    The same object as the weekday profile, one period longer: a recurring
    shape, not a year-over-year level, which is why it belongs on Habits rather
    than History. Pooling is what makes the seasonal signal visible — eleven
    Julys say something no single July can — and the point of the chart is to
    read the header year against that shape, so the year is always in front of
    it.

    **No converter, deliberately.** The rate is a ratio and the intensity is a
    harm metric that stays in Std Av, so the drink-type dropdown reaches neither
    series. ``YearComparison`` on History *does* take a converter, and the
    asymmetry looks like an oversight until you notice the two charts plot
    different kinds of number.

    **Which years get pooled is the user's call.** A user whose early years hold
    one row per month would see that era wreck the profile, and the app has no
    multi-user-safe way to tell those years apart from sparse honest ones. So it
    does not try: the range is theirs to narrow, and each layer is labelled with
    whatever it ends up being.
    """

    @classmethod
    def build(
        cls, user, year: int, pooled: PooledRange = NoPooledRange()
    ) -> TypicalYearChartViewModel:
        """The header year, and the pooled range behind it if one was asked for.

        A query a layer, so the header year alone costs one: the pooled range
        may not contain that year, which rules out reading both layers off a
        single span.
        """
        service = DrinkModelService(user)

        return TypicalYearBuilder(
            # the header year is the same operation over one year, so it is the
            # same kind of range — pooled over a span of exactly one
            year=PooledRange(year, year).profile(service),
            pooled=pooled.profile(service),
        ).chart()


class TypicalYearBuilder:
    def __init__(self, year: TypicalYearProfile, pooled: TypicalYearProfile):
        self._year = year
        self._pooled = pooled

    def chart(self) -> TypicalYearChartViewModel:
        return TypicalYearChartViewModel(
            categories=list(month_names().values()),
            year=self._layer(self._year),
            pooled=self._layer(self._pooled),
            heavy_threshold=HEAVY_DAY_STDAV,
            year_from=self._pooled.year_from,
            year_to=self._pooled.year_to,
            text={
                "title": _("Typical year"),
                "share": _("Drinking-day rate"),
                "share_unit": "%",
                "intensity": _("Per drinking day"),
                # not display_unit: the Heavy day plot line is defined in Std Av,
                # and a converted series leaves it marking nothing
                "intensity_unit": "Std Av",
                "threshold_label": _("Heavy day"),
            },
        )

    @classmethod
    def _layer(cls, profile: TypicalYearProfile) -> ProfileLayer:
        if not profile.has_data:
            return ProfileLayer()

        points = profile.points

        return ProfileLayer(
            drinking_day_share=[
                cls._value(point, point.drinking_day_share * 100) for point in points
            ],
            intensity=[cls._value(point, point.intensity) for point in points],
            label=cls._label(profile),
        )

    @staticmethod
    def _value(point: MonthPoint, value: float) -> float | None:
        """A month no pooled year has reached yet has no reading, and a chart
        draws that as a gap.

        The one place this layer carries a null, and it earns it: a running
        year's December plotted as 0.0 is indistinguishable from a December the
        user got through without a Drink, and Highcharts has no other way to
        break a line.
        """
        if not point.calendar_days:
            return None

        return round(value, 1)

    @staticmethod
    def _label(profile: TypicalYearProfile) -> str:
        """The years this layer was actually drawn from, named in the legend.

        A narrowed range must never read as covering everything, and with two
        layers on one chart neither may read as the other — so each states its
        own span rather than leaving it to be inferred from the tab.
        """
        year_from, year_to = profile.year_from, profile.year_to

        if year_from == year_to:
            return str(year_to)

        return _("Pooled %(year_from)s–%(year_to)s") % {
            "year_from": year_from,
            "year_to": year_to,
        }
