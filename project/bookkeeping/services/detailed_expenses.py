from datetime import date

import polars as pl
from django.utils.text import slugify
from django.utils.translation import gettext as _


class Service:
    MONTHS = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    VALID_ORDERS = {"title", "total", "max_col"}

    def __init__(self, year, data, order="title"):
        self.year = year
        self._data = data
        self._order = self._determine_order(order)
        self._month = self._get_month_index(order)
        self._category = self._get_category(data)

    def _determine_order(self, order):
        order = order.lower()
        if order in self.MONTHS:
            return "month"

        return order if order in self.VALID_ORDERS else "title"

    def _get_month_index(self, order):
        return self.MONTHS.index(order.lower()) if order.lower() in self.MONTHS else 0

    @property
    def context(self):
        if not self._data:
            return {}

        data = self._insert_missing_data(self._data)
        df = self._create_df(data, self._month)
        df = self._sort_dataframe(df)

        return self._build_context(df)

    def _insert_missing_data(self, data):
        required_dates = [date(self.year, 1, 1), date(self.year, 12, 1)]
        existing_entries = {(entry["title"], entry["date"]) for entry in data}
        titles = {entry["title"] for entry in data}

        # Add missing entries for required dates
        missing_data = [
            {"date": month_date, "sum": 0, "title": title, "type_title": self._category}
            for title in titles
            for month_date in required_dates
            if (title, month_date) not in existing_entries
        ]
        return data + missing_data

    def _create_df(self, data, month):
        """
        Create a Polars DataFrame with required transformations.
        """
        return (
            pl.DataFrame(data)
            .drop("type_title")
            .sort(["date", "title"])
            .upsample(
                time_column="date", group_by="title", every="1mo", maintain_order=True
            )
            .with_columns(pl.col("title").forward_fill())
            .fill_null(0.0)
            .with_columns(pl.col("sum").sum().over("date").alias("total_row"))
            .with_columns(pl.col("sum").sum().over("title").alias("total_col"))
            .with_columns(
                pl.col("sum")
                .implode()
                .over("title", mapping_strategy="join")
                .flatten()
                .list.get(month)
                .alias("max_selected_month_value")
            )
        )

    def _sort_dataframe(self, df):
        if self._order == "title":
            return df.sort(["title", "date"])

        if self._order == "month":
            return df.sort(
                [-pl.col.max_selected_month_value, pl.col.title, pl.col.date]
            )

        if self._order == "total":
            return df.sort([-pl.col.total_col, pl.col.title, pl.col.date])

        return df

    def _build_context(self, df):
        type_title = self._data[0]["type_title"]
        context_item = {
            "name": f"{_('Expenses')} / {type_title}",
            "slug": slugify(type_title),
            "items": [],
            "total": 0,
            "total_col": [],
            "total_row": [],
        }

        for df_part in df.partition_by("title"):
            total_col = df_part["total_col"][0]
            context_item["total"] += total_col
            context_item["total_col"].append(total_col)
            context_item["total_row"] = df_part["total_row"].to_list()
            context_item["items"].append(
                {"title": df_part["title"][0], "data": df_part["sum"].to_list()}
            )
        return context_item

    def _get_category(self, data):
        return data[0].get("type_title") if data and isinstance(data, list) else None
