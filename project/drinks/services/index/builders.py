from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from django.utils.translation import gettext as _

from ....core.lib.date import ydays
from ....core.lib.translation import month_names
from ...lib.drinks_stats import DrinkStats

if TYPE_CHECKING:
    from ...lib.drinks_options import DrinksOptions


class IndexBuilder:
    """Pure presentation logic — builds chart/table dicts from DrinkStats data."""

    def __init__(
        self,
        options: DrinksOptions,
        drink_stats: DrinkStats,
        target: float = 0.0,
        latest_past_date: date | None = None,
        latest_current_date: date | None = None,
    ):
        self._target = target
        self._latest_past_date = latest_past_date
        self._latest_current_date = latest_current_date

        self._drink_stats = drink_stats
        self._per_day_of_year = drink_stats.per_day_of_year
        self._quantity_of_year = drink_stats.qty_of_year

        self._options = options

    def chart_quantity(self) -> dict:
        return {
            "categories": list(month_names().values()),
            "data": self._drink_stats.qty_of_month,
            "text": {"quantity": _("Quantity")},
        }

    def chart_consumption(self) -> dict:
        return {
            "categories": list(month_names().values()),
            "data": self._drink_stats.per_day_of_month,
            "target": self._target,
            "avg": self._per_day_of_year,
            "text": {
                "limit": _("Limit"),
                "alcohol": _("Alcohol consumption per day, milliliters"),
            },
        }

    def tbl_dry_days(self) -> dict:
        _dict = {}

        if latest := self._latest_current_date or self._latest_past_date:
            delta = (datetime.now().date() - latest).days
            _dict = {"date": latest, "delta": delta}

        return _dict

    def tbl_consumption(self) -> dict:
        return {
            "qty": self._quantity_of_year,
            "avg": self._per_day_of_year,
            "target": self._target,
        }

    def tbl_alcohol(self) -> dict:
        stdav = self._quantity_of_year / self._options.ratio

        return {"liters": self._options.stdav_to_alcohol(stdav)}

    def tbl_std_av(self) -> dict:
        return {"items": self._build_conversion_rows(self._drink_stats.year, self._quantity_of_year)}

    def _build_conversion_rows(self, year: int, qty: float) -> list[dict]:
        if not qty:
            return {}

        (day, week, month) = self._get_period_counts(year)

        a = {
            "total": qty,
            "per_day": qty / day,
            "per_week": qty / week,
            "per_month": qty / month,
        }

        return [
            {
                "title": _("Beer") + ", 0.5L",
                **{k: self._options.convert(v, "beer") for k, v in a.items()},
            },
            {
                "title": _("Wine") + ", 0.75L",
                **{k: self._options.convert(v, "wine") for k, v in a.items()},
            },
            {
                "title": _("Vodka") + ", 1L",
                **{k: self._options.convert(v, "vodka") for k, v in a.items()},
            },
            {"title": "Std Av", **{k: v * self._options.stdav for k, v in a.items()}},
        ]

    def _get_period_counts(self, year: int) -> tuple[int, int, int]:
        now = datetime.now().date()
        year = year or now.year

        _year = now.year
        _month = now.month
        _week = int(now.strftime("%V"))
        _day = now.timetuple().tm_yday

        if _year == year:
            return (_day, _week, _month)

        _days = ydays(year)
        _weeks = date(year, 12, 28).isocalendar()[1]

        return (_days, _weeks, 12)
