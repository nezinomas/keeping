from dataclasses import dataclass, field
from datetime import datetime

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet


@dataclass(frozen=True)
class HistoryService:
    data: DrinkQuerySet.sum_by_year = None
    years: list[int] = field(default_factory=list)
    alcohol: list[float] = field(default_factory=list)
    per_day: list[float] = field(default_factory=list)
    drink_options: DrinksOptions = field(default_factory=DrinksOptions)

    def __post_init__(self):
        if not self.data:
            return

        self._calc()

    def _calc(self) -> None:
        _first_year = self.data[0]['year']
        _last_year = datetime.now().year + 1

        for _year in range(_first_year, _last_year):
            self.years.append(_year)

            if item := next((x for x in self.data if x['year'] == _year), False):
                _days = ydays(_year)
                _stdav = item['qty']

                self.alcohol.append(
                    self.drink_options.stdav_to_alcohol(_stdav)
                )
                self.per_day.append(
                    self.drink_options.stdav_to_ml(
                        _stdav, self.drink_options.drink_type) / _days
                )
            else:
                self.alcohol.append(0.0)
                self.per_day.append(0.0)
