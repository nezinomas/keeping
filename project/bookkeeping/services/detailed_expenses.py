from datetime import date
import polars as pl
from django.utils.translation import gettext as _


class Service:
    def __init__(self, year, data, order):
        self.year = year
        self._data = data
        self._order = "title"
        self._month = 0

        months = [
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

        orders = [
            "title",
            "total",
        ]

        order = order.lower()

        if order in months:
            self._order = "month"
            self._month = months.index(order)

        if order in orders:
            self._order = order

    @property
    def context(self):
        if not self._data:
            return {}

        data = self._insert_missing_data(self._data)
        df = self._create_df(data, self._month)

        if self._order == "title":
            df = df.sort(["title", "date"])

        if self._order == "month":
            df = df.sort(
                [-pl.col.max_seletected_month_value, pl.col.title, pl.col.date]
            )

        if self._order == "total":
            df = df.sort([-pl.col.total_col, pl.col.title, pl.col.date])

        context_item = {
            "name": f"{_('Expenses')} / {self._data[0]['type_title']}",
            "items": [],
            "total": 0,
            "total_col": [],
            "total_row": [],
        }

        for df_part in df.partition_by("title"):
            total_col = df_part["total_col"][0]
            context_item["total"] += total_col
            context_item["total_col"] += [total_col]
            context_item["total_row"] = df_part["total_row"].to_list()
            context_item["items"] += [
                {"title": df_part["title"][0], "data": df_part["sum"].to_list()}
            ]
        return context_item

    def _create_df(self, data, month):
        return (
            pl.DataFrame(data)
            .drop("type_title")
            .sort(["date", "title"])
            .upsample(
                time_column="date", group_by="title", every="1mo", maintain_order=True
            )
            .with_columns(pl.col("title").forward_fill())
            .fill_null(0.0)
            .with_columns(pl.col.sum.sum().over([pl.col.date]).alias("total_row"))
            .with_columns(pl.col.sum.sum().over([pl.col.title]).alias("total_col"))
            .with_columns(
                pl.col("sum")
                .implode()
                .over("title", mapping_strategy="join")
                .flatten()
                .list.get(month)
                .alias("max_seletected_month_value")
            )
        )

    def _insert_missing_data(self, data):
        required_dates = [date(self.year, 1, 1), date(self.year, 12, 1)]

        # Track existing entries
        existing_entries = {(entry["title"], entry["date"]) for entry in data}

        titles = {entry["title"] for entry in data}  # Extract unique titles

        data.extend(
            {"date": month_date, "sum": 0, "title": title, "type_title": "type1"}
            for title in titles
            for month_date in required_dates
            if (title, month_date) not in existing_entries
        )

        return data
