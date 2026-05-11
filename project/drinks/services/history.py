from datetime import datetime

import polars as pl
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from ...users.models import User
from ..lib.drinks_options import DrinkConverter
from ..services.model_services import DrinkModelService


class HistoryService:
    def __init__(self, user: User, data: list[dict]):
        self.history_df: pl.DataFrame = pl.DataFrame()
        self.converter: DrinkConverter = DrinkConverter(user.drink_type)

        if data:
            if isinstance(data, QuerySet):
                data = list(data)

            self.history_df = self._prepare_data_frame(data)

    @property
    def years(self) -> list[int]:
        return self._data_frame_column("year")

    @property
    def alcohol(self) -> list[float]:
        return self._data_frame_column("alcohol")

    @property
    def per_day(self) -> list[float]:
        return self._data_frame_column("per_day")

    @property
    def quantity(self) -> list[int]:
        return self._data_frame_column("qty")

    def _prepare_data_frame(self, data) -> pl.DataFrame:
        history_df = pl.DataFrame(data).lazy()

        if not history_df.collect().is_empty():
            start_year = history_df.select(pl.col.year.min()).collect().item()
            end_year = datetime.now().year
            years_df = pl.DataFrame({"year": range(start_year, end_year + 1)}).lazy()
            history_df = years_df.join(history_df, on="year", how="left").fill_null(0)

        return (
            self._aggregate_by_year(history_df)
            .with_columns(date=pl.date("year", 1, 1))
            .pipe(self._calculate_days_in_year)
            .pipe(self._calculate_consumption_stats)
            .sort(pl.col.year)
            .collect()
        )

    def _aggregate_by_year(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.group_by("year").agg(pl.col.qty.sum(), pl.col.stdav.sum())

    def _calculate_consumption_stats(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.with_columns(
            alcohol=self.converter.stdav_to_alcohol(pl.col.stdav),
            ml=self.converter.stdav_to_ml(pl.col.stdav),
        ).with_columns(per_day=pl.col.ml / pl.col.days_in_year)

    def _calculate_days_in_year(self, df: pl.LazyFrame) -> pl.LazyFrame:
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

    def _data_frame_column(self, column_name: str) -> list:
        return (
            self.history_df[column_name].to_list()
            if not self.history_df.is_empty()
            else []
        )


def load_service(user) -> dict:
    data = DrinkModelService(user).sum_by_year()
    service = HistoryService(user, data)

    return {
        "records": len(service.years) if len(service.years) > 1 else 0,
        "chart": {
            "categories": service.years,
            "data_ml": service.per_day,
            "data_alcohol": service.alcohol,
            "text": {
                "title": _("Drinks"),
                "per_day": _("Average per day, ml"),
                "per_year": _("Pure alcohol per year, L"),
            },
        },
    }
