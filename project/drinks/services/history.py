from datetime import datetime

import polars as pl
from django.utils.translation import gettext as _

from .. import models
from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet


class HistoryService:
    def __init__(self, data):
        self._df = pl.DataFrame()
        self.options = DrinksOptions()

        if data:
            if isinstance(data, DrinkQuerySet):
                data = list(data)
            self._df = self._calc(data)

    @staticmethod
    def insert_empty_values(data: list[dict]) -> list[dict]:
        first_year = data[0]["year"]
        last_year = datetime.now().year + 1

        for year in range(first_year, last_year):
            data.append({"year": year, "qty": 0, "stdav": 0.0})

        return data

    def _create_df(self, data) -> pl.DataFrame:
        data = self.insert_empty_values(data)

        df = pl.DataFrame(data).lazy()
        df = self._agg_df(df)
        df = df.with_columns(date=pl.date("year", 1, 1))
        df = self._days_in_year(df)
        df = self._calc_stats(df)
        df = df.sort(pl.col.year)

        return df.collect()

    def _agg_df(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.group_by("year").agg(pl.col.qty.sum(), pl.col.stdav.sum())

    def _calc_stats(self, df) -> pl.LazyFrame:
        drink_type = self.options.drink_type

        return (
            df
            # calculate alcohol and ml
            .with_columns(
                alcohol=self.options.stdav_to_alcohol(pl.col.stdav),
                ml=self.options.stdav_to_ml(pl.col.stdav, drink_type),
            )
            # calculate per_day
            .with_columns(per_day=pl.col.ml / pl.col.days_in_year)
        )

    def _days_in_year(self, df) -> pl.LazyFrame:
        year = datetime.now().year
        days = datetime.now().timetuple().tm_yday

        return (
            df
            # calculate days_in_year for each year
            .with_columns(
                days_in_year=pl.when(pl.col.date.dt.is_leap_year())
                .then(pl.lit(366))
                .otherwise(pl.lit(365))
            )
            # for current year update days_in_year to actual number of days
            .with_columns(
                days_in_year=pl.when(pl.col.year == year)
                .then(pl.lit(days))
                .otherwise(pl.col.days_in_year)
            )
        )

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
