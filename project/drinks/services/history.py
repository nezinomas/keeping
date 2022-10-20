from dataclasses import dataclass, field
from datetime import datetime

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet


@dataclass(frozen=True)
class HistoryService:
    data: DrinkQuerySet.sum_by_year = None

    years: list[int] = \
        field(init=False, default_factory=list)
    alcohol: list[float] = \
        field(init=False, default_factory=list)
    per_day: list[float] = \
        field(init=False, default_factory=list)
    quantity: list[float] = \
        field(init=False, default_factory=list)
    drink_options: DrinksOptions = \
        field(init=False, default_factory=DrinksOptions)

    def __post_init__(self):
        if not self.data:
            return

        self._calc()

    def _calc(self) -> None:
        _first_year = self.data[0]['year']
        _last_year = datetime.now().year + 1

        for _year in range(_first_year, _last_year):
            _quantity = 0.0
            _alcohol = 0.0
            _per_day = 0.0

            if item := next((x for x in self.data if x['year'] == _year), False):
                _stdav = item['qty']
                _ml = self.drink_options.stdav_to_ml(_stdav, self.drink_options.drink_type)
                _quantity = self.drink_options.ratio * _stdav
                _alcohol = self.drink_options.stdav_to_alcohol(_stdav)

                # mililitres per day
                # for current year get day number, else 365 or 366
                _date = datetime.now().date()
                if _year == _date.year:
                    _day_of_year = _date.timetuple().tm_yday
                else:
                    _day_of_year = ydays(_year)

                _per_day = _ml / _day_of_year

            self.years.append(_year)
            self.quantity.append(_quantity)
            self.alcohol.append(_alcohol)
            self.per_day.append(_per_day)
