from dataclasses import dataclass, field
from datetime import datetime

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet


@dataclass()
class HistoryService:
    data: DrinkQuerySet.sum_by_year = None

    years: list[int] = \
        field(init=False, default_factory=list)
    alcohol: list[float] = \
        field(init=False, default_factory=list)
    per_day: list[float] = \
        field(init=False, default_factory=list)
    avg_ml_per_day: float = \
        field(init=False, default=0.0)
    quantity: list[float] = \
        field(init=False, default_factory=list)
    total_quantity: float = \
        field(init=False, default=0.0)
    drink_options: DrinksOptions = \
        field(init=False, default_factory=DrinksOptions)

    def __post_init__(self):
        if not self.data:
            return

        self._calc()
        self._set_current_year_values()

    def _calc(self) -> None:
        _first_year = self.data[0]['year']
        _last_year = datetime.now().year + 1

        for _year in range(_first_year, _last_year):
            _quantity = 0.0
            _alcohol = 0.0
            _per_day = 0.0

            if item := next((x for x in self.data if x['year'] == _year), False):
                _stdav = item['stdav']
                _quantity = item['qty']
                _ml = self.drink_options.stdav_to_ml(_stdav, self.drink_options.drink_type)
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

    def _set_current_year_values(self):
        _year = datetime.now().date().year
        _idx =  self.years.index(_year)

        self.total_quantity = self.quantity[_idx]
        self.avg_ml_per_day = self.per_day[_idx]
