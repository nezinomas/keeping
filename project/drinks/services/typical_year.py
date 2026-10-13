import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from itertools import takewhile

from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from ...core.lib.year_boundary import YearBoundary
from ..lib.drinks_risk import HEAVY_DAY_STDAV
from .model_services import DrinkModelService
from .profile_chart import ProfileLayer, profile_chart_dict, profile_chart_text

MONTHS = 12


@dataclass(frozen=True)
class MonthTotal:
    """One month of one year as the DB aggregates it: the Std Av, and the Drinking
    days it was spread over. Neither implies the other."""

    year: int
    month: int  # 1 = January
    stdav: float
    drinking_days: int


@dataclass(frozen=True)
class MonthPoint:
    """One pooled month. ``calendar_days``, the rate's denominator, counts only the
    days of that month each pooled year has reached."""

    month: int  # 1 = January
    calendar_days: int
    drinking_days: int
    stdav: float
    drinking_day_share: float  # drinking_days / calendar_days
    intensity: float  # stdav / drinking_days


@dataclass(frozen=True)
class TypicalYearProfile:
    """Twelve months pooled across a span of years. Pure: rows and ``today`` in."""

    points: list[MonthPoint]
    year_from: int = 0
    year_to: int = 0

    @property
    def has_data(self) -> bool:
        return bool(self.year_to)

    @property
    def reached_points(self) -> list[MonthPoint]:
        """The months some pooled year has reached; only the running year stops."""
        return list(takewhile(lambda point: point.calendar_days, self.points))

    @classmethod
    def pool(cls, rows: Sequence[MonthTotal], today: date) -> "TypicalYearProfile":
        """Only years carrying a Drink add days: an unlogged year is not abstinence."""
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
    def _days_reached(year: int, month: int, today: date) -> int:
        """The days of one month of one year the calendar has reached: a finished
        year runs to Dec 31, the running one only to today."""
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
    """The years a pooled layer is drawn from, the user's explicit ask; zeros mean
    every year on record."""

    year_from: int = 0
    year_to: int = 0

    @classmethod
    def resolve(cls, year: int, qty: int) -> "PooledRange":
        if not qty:
            return cls()

        return cls(year - qty + 1, year)

    def profile(self, service: DrinkModelService, today: date) -> TypicalYearProfile:
        """One query however many years are pooled: the DB groups, this pools."""
        rows = [
            MonthTotal(**row)
            for row in service.sum_by_year_month(self.year_from, self.year_to)
        ]

        return TypicalYearProfile.pool(rows, today)


class NoPooledRange(PooledRange):
    """Nothing pooled: the chart opens on the header year alone, at no query.
    Pooling a decade behind the year is a reading to ask for, not to be given."""

    def profile(self, service: DrinkModelService, today: date) -> TypicalYearProfile:
        return TypicalYearProfile.pool([], today)


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
        """Back to front: the pooled range is the backdrop the header year is read
        against."""
        return [layer for layer in (self.pooled, self.year) if layer.has_data]

    @property
    def as_dict(self) -> dict:
        return profile_chart_dict(self)


class TypicalYear:
    """The header year, in front of a pooled range the user chose to ask for.
    No converter: the rate is a ratio and the intensity a Std Av harm metric."""

    @classmethod
    def build(
        cls, user, year: int, today: date, pooled: PooledRange = NoPooledRange()
    ) -> TypicalYearChartViewModel:
        """The header year, and the pooled range behind it if one was asked for.
        A query a layer: the range may not contain the header year."""
        service = DrinkModelService(user)

        return TypicalYearBuilder(
            year=PooledRange(year, year).profile(service, today),
            pooled=pooled.profile(service, today),
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
            text=profile_chart_text(),
        )

    @classmethod
    def _layer(cls, profile: TypicalYearProfile) -> ProfileLayer:
        if not profile.has_data:
            return ProfileLayer()

        return ProfileLayer.from_points(profile.reached_points, cls._label(profile))

    @staticmethod
    def _label(profile: TypicalYearProfile) -> str:
        """The span this layer was drawn from, so a narrowed range never reads as
        everything and neither of two layers reads as the other."""
        year_from, year_to = profile.year_from, profile.year_to

        if year_from == year_to:
            return str(year_to)

        return _("Pooled %(year_from)s–%(year_to)s") % {
            "year_from": year_from,
            "year_to": year_to,
        }
