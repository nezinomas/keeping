import contextlib
from datetime import date, datetime
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from ...core.lib.date import ydays
from ...core.lib.translation import month_names
from ..lib.drinks_options import DrinksOptions
from ..lib.drinks_stats import DrinkStats
from ..managers import DrinkQuerySet
from ..models import Drink, DrinkTarget


class IndexServiceData:
    sum_by_month: DrinkQuerySet.sum_by_month = None
    sum_by_day: DrinkQuerySet.sum_by_day = None

    target: float = 0.0
    latest_past_date: date = None
    latest_current_date: date = None

    def __init__(self, year):
        self.sum_by_month = Drink.objects.sum_by_month(year)
        self.sum_by_day = Drink.objects.sum_by_day(year)

        with contextlib.suppress(Drink.DoesNotExist):
            self.latest_past_date = (
                Drink.objects.related().filter(date__year__lt=year).latest().date
            )

        with contextlib.suppress(Drink.DoesNotExist):
            self.latest_current_date = Drink.objects.year(year).latest().date

        with contextlib.suppress(DrinkTarget.DoesNotExist):
            self.target = DrinkTarget.objects.year(year).get(year=year).qty


class IndexService:
    def __init__(
        self,
        drink_stats: DrinkStats,
        target: float = 0.0,
        latest_past_date: date = None,
        latest_current_date: date = None,
    ):
        self._target = target
        self._latest_past_date = latest_past_date
        self._latest_current_date = latest_current_date

        self._drink_stats = drink_stats
        self._per_day_of_year = drink_stats.per_day_of_year
        self._quantity_of_year = drink_stats.qty_of_year

        self._options = DrinksOptions()

    def chart_quantity(self) -> List[Dict]:
        return {
            "categories": list(month_names().values()),
            "data": self._drink_stats.qty_of_month,
            "text": {"quantity": _("Quantity")},
        }

    def chart_consumption(self) -> str:
        return {
            "categories": list(month_names().values()),
            "data": self._drink_stats.per_day_of_month,
            "target": self._target,
            "avg": self._per_day_of_year,
            "avg_label_y": self._avg_label_position(
                self._per_day_of_year, self._target
            ),
            "target_label_y": self._target_label_position(
                self._per_day_of_year, self._target
            ),
            "text": {
                "limit": _("Limit"),
                "alcohol": _("Alcohol consumption per day, ml"),
            },
        }

    def tbl_dry_days(self) -> Dict:
        _dict = {}

        if latest := self._latest_current_date or self._latest_past_date:
            delta = (datetime.now().date() - latest).days
            _dict = {"date": latest, "delta": delta}

        return _dict

    def tbl_consumption(self) -> str:
        return {
            "qty": self._quantity_of_year,
            "avg": self._per_day_of_year,
            "target": self._target,
        }

    def tbl_alcohol(self) -> str:
        stdav = self._quantity_of_year / self._options.ratio

        return {"liters": self._options.stdav_to_alcohol(stdav)}

    def tbl_std_av(self) -> str:
        return {"items": self._std_av(self._drink_stats.year, self._quantity_of_year)}

    def _avg_label_position(self, avg: float, target: float) -> int:
        return 15 if target - 50 <= avg <= target else -5

    def _target_label_position(self, avg: float, target: float) -> int:
        return 15 if avg - 50 <= target <= avg else -5

    def _std_av(self, year: int, qty: float) -> List[Dict]:
        if not qty:
            return {}

        (day, week, month) = self._dates(year)

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

    def _dates(self, year: int) -> Tuple[int, int, int]:
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
