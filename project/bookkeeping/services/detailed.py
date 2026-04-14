from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from functools import cached_property

import polars as pl
from django.utils.text import slugify
from django.utils.translation import gettext as _

from ...expenses.services.model_services import (
    ExpenseModelService,
)
from ...incomes.services.model_services import (
    IncomeModelService,
)
from ...savings.services.model_services import SavingModelService
from ...users.models import User


@dataclass(frozen=True)
class DetailedDto:
    data: list[dict]


class DetailedDataProvider:
    def __init__(self, user: User):
        self.user = user
        self.year = user.year

    def get_incomes(self) -> DetailedDto:
        return DetailedDto(
            data=list(IncomeModelService(self.user).sum_by_month_and_type(self.year))
        )

    def get_savings(self) -> DetailedDto:
        return DetailedDto(
            data=list(SavingModelService(self.user).sum_by_month_and_type(self.year))
        )

    def get_expenses(self) -> dict[str, DetailedDto]:
        """Returns a dictionary mapping expense categories to their respective DTOs."""
        qs = ExpenseModelService(self.user).sum_by_month_and_name(self.year)

        grouped_data = defaultdict(list)
        for record in qs:
            group_key = record.pop("type_title")
            grouped_data[group_key].append(record)

        return {title: DetailedDto(data=data) for title, data in grouped_data.items()}


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

        # Copy data to avoid mutating the frozen DTO
        data = list(self.dto.data)
        unique_titles = {item["title"] for item in data}

        # Empty sums for December. This is a hack for polars upsample method
        for title in unique_titles:
            data.append({"date": date(self.year, 12, 1), "sum": 0, "title": title})

        df = (
            pl.DataFrame(data)
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

    def _apply_sorting(self, df: pl.DataFrame) -> pl.DataFrame:
        """Applies dynamic sorting based on the instance's order parameter."""
        if not self.order:
            return df

        descending = self.order.startswith("-")
        sort_col = self.order.lstrip("-")

        # Prevent crashes if the requested sort column doesn't exist
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


class DetailedContextPresenter:
    """Formats a TableBuilder into the exact dictionary structure required by the UI."""

    @staticmethod
    def build(title: str, url_title: str, dto: DetailedDto, year: int) -> dict:
        builder = DetailedTableBuilder(dto, year)
        return {
            "title": title,
            "url_title": url_title,
            "data": builder.table,
            "total": builder.total_row,
        }


def load_service(user: User) -> dict:
    year = user.year
    provider = DetailedDataProvider(user)

    # Build Expense contexts dynamically
    expense_contexts = [
        DetailedContextPresenter.build(
            title=f"{_('Expenses')} / {expense_type_title}",
            url_title=slugify(expense_type_title),
            dto=dto,
            year=year,
        )
        for expense_type_title, dto in provider.get_expenses().items()
    ]

    return {
        "income": DetailedContextPresenter.build(
            title=_("Incomes"),
            url_title="income",
            dto=provider.get_incomes(),
            year=year,
        ),
        "saving": DetailedContextPresenter.build(
            title=_("Savings"),
            url_title="saving",
            dto=provider.get_savings(),
            year=year,
        ),
        "expense": expense_contexts,
    }
