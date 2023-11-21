from datetime import datetime

import polars as pl
from django.utils.translation import gettext as _

from .. import models
from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet


class HistoryService:
    def __init__(self, data):
        self._df = pl.DataFrame()

        if not data:
            return

        if isinstance(data, DrinkQuerySet):
            data = list(data)

        self.options = DrinksOptions()
        self._df = self._calc(data)

    @staticmethod
    def insert_empty_values(data: list[dict]) -> list[dict]:
        first_year = data[0]["year"]
        last_year = datetime.now().year + 1

        for year in range(first_year, last_year):
            data.append({"year": year, "qty": 0, "stdav": 0.0})

        return data

    def _calc(self, data) -> pl.DataFrame:
        data = __class__.insert_empty_values(data)

        year_ = datetime.now().year
        days_ = datetime.now().timetuple().tm_yday

        df = pl.DataFrame(data)
        return (
            df.lazy()
            .group_by("year")
            .agg(pl.col.qty.sum(), pl.col.stdav.sum())
            .with_columns(date = pl.date("year", 1, 1))
            # calculate days_in_year for each year
            .with_columns(
                days_in_year =
                pl.when(pl.col.date.dt.is_leap_year())
                .then(pl.lit(366))
                .otherwise(pl.lit(365))
            )
            # for current year update days_in_year to actual number of days
            .with_columns(
                days_in_year =
                pl.when(pl.col.year == year_)
                .then(pl.lit(days_))
                .otherwise(pl.col.days_in_year)
            )
            # calculate alcohol and ml
            .with_columns(
                alcohol = self.options.stdav_to_alcohol(pl.col.stdav),
                ml = self.options.stdav_to_ml(pl.col.stdav, self.options.drink_type),
            )
            # calculate per_day
            .with_columns(per_day = (pl.col.ml / pl.col.days_in_year))
            .sort(pl.col.year)
        ).collect()

    def _data_frame_col(self, col: str) -> list:
        return self._df[col].to_list() if not self._df.is_empty() else []

    @property
    def years(self) -> list[int]:
        return self._data_frame_col("year")

    @property
    def alcohol(self) -> list[float]:
        return self._data_frame_col("alcohol")

    @property
    def per_day(self) -> list[float]:
        return self._data_frame_col("per_day")

    @property
    def quantity(self) -> list[int]:
        return self._data_frame_col("qty")


def load_service() -> dict:
    data = models.Drink.objects.sum_by_year()
    obj = HistoryService(data)

    return {
        "tab": "history",
        "records": len(obj.years) if len(obj.years) > 1 else 0,
        "chart": {
            "categories": obj.years,
            "data_ml": obj.per_day,
            "data_alcohol": obj.alcohol,
            "text": {
                "title": _("Drinks"),
                "per_day": _("Average per day, ml"),
                "per_year": _("Pure alcohol per year, L"),
            },
        },
    }
