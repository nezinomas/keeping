from datetime import date
from functools import cached_property

import polars as pl

from .dtos import DetailedDto


class DetailedTableBuilder:
    """Takes a DTO and constructs the Polars pivot table with dynamic sorting."""

    def __init__(self, dto: DetailedDto, year: int, order: str = ""):
        self.dto = dto
        self.year = year
        self.order = order

    @cached_property
    def df(self) -> pl.DataFrame:
        if not self.dto.data:
            return pl.DataFrame()

        padded_data = self._pad_data_for_upsampling(list(self.dto.data))

        base_df = (
            pl.DataFrame(padded_data)
            .upsample(
                time_column="date", group_by="title", every="1mo", maintain_order=True
            )
            .with_columns(pl.col("sum").fill_null(0))
            .group_by("title", "date")
            .agg(pl.col("sum").sum())
            .sort(["title", "date"])
            .with_columns(date=(pl.col("date").dt.month()))
            .pivot(index="title", on="date", values="sum", aggregate_function="sum")
            .fill_null(0)
            .with_columns(total_col=pl.sum_horizontal(pl.exclude("title")))
        )

        return self._apply_sorting(base_df)

    def _pad_data_for_upsampling(self, data: list[dict]) -> list[dict]:
        """Adds empty December records to ensure Polars upsamples the entire year."""
        unique_titles = {item["title"] for item in data}

        for title in unique_titles:
            data.append({"date": date(self.year, 12, 1), "sum": 0, "title": title})

        return data

    def _apply_sorting(self, df: pl.DataFrame) -> pl.DataFrame:
        """Applies dynamic sorting based on the instance's order parameter."""
        if not self.order:
            return df

        descending = self.order.startswith("-")
        sort_col = self.order.lstrip("-")

        if sort_col in df.columns:
            return df.sort(sort_col, descending=descending)

        return df

    @property
    def table(self) -> list[dict]:
        return [] if self.df.is_empty() else self.df.to_dicts()

    @property
    def total_row(self) -> dict:
        if self.df.is_empty():
            return {}
        return self.df.select(pl.all().exclude("title").sum()).to_dicts()[0]
