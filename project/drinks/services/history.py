from collections.abc import Iterable
from datetime import date

import polars as pl
from django.utils.translation import gettext as _

from ...core.lib.date import ydays
from ...users.models import User
from ..lib.drinks_options import DrinkConverter, stdav_to_alcohol
from ..services.model_services import DrinkModelService


class HistoryService:
    def __init__(self, user: User, data: Iterable[dict], today: date):
        self.converter: DrinkConverter = DrinkConverter(user.drink_type)
        self._header_year: int = user.year
        self._today = today
        self._days_elapsed = today.timetuple().tm_yday

        rows = list(data)
        self.history_df: pl.DataFrame = pl.DataFrame()
        if rows:
            self.history_df = self._prepare_data_frame(rows)

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

    @property
    def forecast(self) -> list[dict]:
        """The running year's straight-line pace of pure alcohol, as one point."""
        calendar_year = self._today.year

        if calendar_year not in self.years:
            return []

        index = self.years.index(calendar_year)
        litres = self.alcohol[index] / self._days_elapsed * ydays(calendar_year)

        return [{"x": index, "y": litres}]

    def _prepare_data_frame(self, data) -> pl.DataFrame:
        history_df = pl.DataFrame(data).lazy()

        if not history_df.collect().is_empty():
            start_year = history_df.select(pl.col.year.min()).collect().item()
            last_recorded = history_df.select(pl.col.year.max()).collect().item()
            # the furthest of the three, so a header year ahead of the calendar
            # year still gets its own column
            end_year = max(self._today.year, self._header_year, last_recorded)
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
        # pure alcohol is a real volume whatever the drink type, but the amount
        # itself is read in the unit the dropdown selects — Std Av as typed
        return df.with_columns(
            alcohol=stdav_to_alcohol(pl.col.stdav),
            shown=self.converter.stdav_to_display(pl.col.stdav),
        ).with_columns(per_day=pl.col.shown / pl.col.days_in_year)

    def _calculate_days_in_year(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.with_columns(
            days_in_year=pl.when(pl.col.date.dt.is_leap_year())
            .then(pl.lit(366))
            .otherwise(pl.lit(365))
        ).with_columns(
            days_in_year=pl.when(pl.col.year == self._today.year)
            .then(pl.lit(self._days_elapsed))
            .otherwise(pl.col.days_in_year)
        )

    def _data_frame_column(self, column_name: str) -> list:
        if self.history_df.is_empty():
            return []

        return self.history_df[column_name].to_list()


def load_service(user, today: date) -> dict:
    data = DrinkModelService(user).sum_by_year()
    service = HistoryService(user, data, today)

    return {
        "records": len(service.years) if len(service.years) > 1 else 0,
        "chart": {
            "categories": service.years,
            "data_ml": service.per_day,
            "data_alcohol": service.alcohol,
            "forecast": service.forecast,
            "unit": service.converter.display_unit,
            "decimals": service.converter.display_decimals,
            "text": {
                "per_day": f"{_('Average per day')}, {service.converter.display_unit}",
                "per_year": _("Pure alcohol per year, L"),
                "forecast": _("Forecast"),
            },
        },
    }
