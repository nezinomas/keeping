from collections import defaultdict
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

        df = (
            pl.DataFrame(padded_data)
            .sort(["title", "date"])
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

        return self._apply_sorting(df)

    def _pad_data_for_upsampling(self, data: list[dict]) -> list[dict]:
        if not data:
            return data

        # Map every title to a set of its existing months
        existing_months_map = defaultdict(set)
        for item in data:
            existing_months_map[item["title"]].add(item["date"].month)

        # Pad missing boundaries using map
        for title, months in existing_months_map.items():
            item = {"sum": 0, "title": title}

            if 1 not in months:
                data.append(item | {"date": date(self.year, 1, 1)})

            if 12 not in months:
                data.append(item | {"date": date(self.year, 12, 1)})

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
