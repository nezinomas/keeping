from datetime import datetime

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinksOptions


class HistoryService:
    def __init__(self, data):
        self._drink_options = DrinksOptions()
        self._calc(data)

    @property
    def years(self):
        return self._years

    @property
    def alcohol(self):
        return self._alcohol

    @property
    def per_day(self):
        return self._per_day

    def _calc(self, data):
        years = []
        alcohol = []
        per_day = []

        if data:
            _range = range(data[0]['year'], datetime.now().year + 1)
            for _year in _range:
                years.append(_year)

                if item := next((x for x in data if x['year'] == _year), False):
                    _days = ydays(_year)
                    _stdav = item['qty']

                    alcohol.append(
                        self._drink_options.stdav_to_alcohol(_stdav)
                    )
                    per_day.append(
                        self._drink_options.stdav_to_ml(
                            _stdav, self._drink_options.drink_type) / _days
                    )
                else:
                    alcohol.append(0.0)
                    per_day.append(0.0)

        self._years = years
        self._alcohol = alcohol
        self._per_day = per_day
