from datetime import datetime

import polars as pl
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from ...users.models import User
from ..lib.drinks_options import DrinkConverter
from ..services.model_services import DrinkModelService


class HistoryService:
    def __init__(self, user: User, data: list[dict]):
        self.df: pl.DataFrame = pl.DataFrame()
        self.converter: DrinkConverter = DrinkConverter(user.drink_type)

        if data:
            if isinstance(data, QuerySet):
                data = list(data)

            self.df = self._create_df(data)


    def _create_df(self, data) -> pl.DataFrame:
        df = pl.DataFrame(data).lazy()

        if not df.collect().is_empty():
            first_year = df.select(pl.col.year.min()).collect().item()
            last_year = datetime.now().year
            years_df = pl.DataFrame({"year": range(first_year, last_year + 1)}).lazy()
            df = years_df.join(df, on="year", how="left").fill_null(0)

        return (
            self._agg_df(df)
            .with_columns(date=pl.date("year", 1, 1))
            .pipe(self._days_in_year)
            .pipe(self._calc_stats)
            .sort(pl.col.year)
            .collect()
        )

    def _agg_df(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.group_by("year").agg(pl.col.qty.sum(), pl.col.stdav.sum())

    def _calc_stats(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return (
            df.with_columns(
                alcohol=self.converter.stdav_to_alcohol(pl.col.stdav),
                ml=self.converter.stdav_to_ml(pl.col.stdav),
            ).with_columns(per_day=pl.col.ml / pl.col.days_in_year)
        )

    def _days_in_year(self, df: pl.LazyFrame) -> pl.LazyFrame:
        now = datetime.now()
        return df.with_columns(
            days_in_year=pl.when(pl.col.date.dt.is_leap_year())
            .then(pl.lit(366))
            .otherwise(pl.lit(365))
        ).with_columns(
            days_in_year=pl.when(pl.col.year == now.year)
            .then(pl.lit(now.timetuple().tm_yday))
            .otherwise(pl.col.days_in_year)
        )

    def _data_frame_col(self, col: str) -> list:
        return self.df[col].to_list() if not self.df.is_empty() else []

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


def load_service(user) -> dict:
    data = DrinkModelService(user).sum_by_year()
    obj = HistoryService(user, data)

    return {
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
