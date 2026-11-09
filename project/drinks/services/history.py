from collections.abc import Iterable
from datetime import date

import polars as pl
from django.utils.translation import gettext as _

from ...core.lib.date import ydays
from ...core.lib.year_boundary import YearBoundary
from ...users.models import User
from ..lib.drinks_options import DrinkConverter, stdav_to_alcohol
from ..services.model_services import DrinkModelService


class HistoryService:
    def __init__(self, year: int, drink_type: str, data: Iterable[dict], today: date):
        self.converter: DrinkConverter = DrinkConverter(drink_type)
        self._year = year
        self._today = today

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
    def per_day(self) -> list[float | None]:
        return self._data_frame_column("per_day")

    @property
    def quantity(self) -> list[int]:
        return self._data_frame_column("qty")

    @property
    def forecast(self) -> list[dict]:
        """The running year's straight-line pace of pure alcohol, as one point."""
        calendar_year = self._today.year
        years = self.years

        if calendar_year not in years:
            return []

        index = years.index(calendar_year)
        days = YearBoundary(calendar_year, self._today).days_elapsed
        litres = self.alcohol[index] / days * ydays(calendar_year)

        return [{"x": index, "y": litres}]

    def _prepare_data_frame(self, rows: list[dict]) -> pl.DataFrame:
        recorded = pl.DataFrame(rows)
        # the furthest of the three, so a Selected year ahead of the calendar
        # year still gets its own column
        end_year = max(self._today.year, self._year, recorded["year"].max())
        years = range(recorded["year"].min(), end_year + 1)
        columns = pl.LazyFrame(
            {
                "year": years,
                "days_elapsed": [
                    YearBoundary(year, self._today).days_elapsed for year in years
                ],
            }
        )

        return (
            columns.join(self._aggregate_by_year(recorded), on="year", how="left")
            .fill_null(0)
            .pipe(self._calculate_consumption_stats)
            .sort(pl.col.year)
            .collect()
        )

    def _aggregate_by_year(self, df: pl.DataFrame) -> pl.LazyFrame:
        return df.lazy().group_by("year").agg(pl.col.qty.sum(), pl.col.stdav.sum())

    def _calculate_consumption_stats(self, df: pl.LazyFrame) -> pl.LazyFrame:
        # pure alcohol is a real volume whatever the drink type, but the amount
        # itself is read in the unit the dropdown selects — Std Av as typed
        return df.with_columns(
            alcohol=stdav_to_alcohol(pl.col.stdav),
            shown=self.converter.stdav_to_display(pl.col.stdav),
        ).with_columns(
            # a Coming year has reached no day: null, Highcharts' gap
            per_day=pl.when(pl.col.days_elapsed > 0).then(
                pl.col.shown / pl.col.days_elapsed
            )
        )

    def _data_frame_column(self, column_name: str) -> list:
        if self.history_df.is_empty():
            return []

        return self.history_df[column_name].to_list()


def load_service(user: User, year: int, drink_type: str, today: date) -> dict:
    running = YearBoundary(today.year, today)
    data = DrinkModelService(user).sum_by_year(running.last_day_reached)
    service = HistoryService(year, drink_type, data, today)
    years = service.years

    return {
        "records": len(years) if len(years) > 1 else 0,
        "chart": {
            "categories": years,
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
