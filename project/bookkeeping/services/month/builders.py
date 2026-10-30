from dataclasses import asdict
from functools import cached_property
from operator import itemgetter

import polars as pl
from django.utils.translation import gettext as _

from ....core.lib.table_columns import DATE, SAVINGS, TOTAL
from .dtos import InfoState


class MonthTableBuilder:
    """Merges the month's expenses and savings into one DataFrame."""

    def __init__(self, expense_df: pl.DataFrame, saving_df: pl.DataFrame):
        self.df = self._build_table(expense_df, saving_df)

    def _build_table(
        self, expense_df: pl.DataFrame, saving_df: pl.DataFrame
    ) -> pl.DataFrame:
        has_expense_types = expense_df.shape[1] > 1

        if has_expense_types:
            expense_df = expense_df.with_columns(
                pl.sum_horizontal(pl.exclude(DATE)).alias(TOTAL)
            )

        return expense_df.join(
            saving_df, on=DATE, how="full", coalesce=True, nulls_equal=True
        ).sort(DATE)

    @cached_property
    def table(self) -> list[dict]:
        return self.df.to_dicts()

    @cached_property
    def total_row(self) -> dict:
        if self.df.is_empty() or self.df.shape[1] == 1:
            return {}
        return self.df.select(pl.exclude(DATE)).sum().to_dicts()[0]


class ChartBuilder:
    """Formats financial data specifically for frontend charts."""

    def __init__(self, targets: dict, totals: dict):
        self.totals = {k: v for k, v in totals.items() if k != TOTAL}
        self.targets = targets

    def build_targets(self) -> dict:
        data = self._sort_chart_data(self.totals)
        categories = [self._upper_title(entry["name"]) for entry in data]
        targets = [self.targets.get(entry["name"], 0) for entry in data]

        return {
            "categories": categories,
            "target": targets,
            "targetTitle": _("Plan"),
            "fact": [
                {"y": entry["y"], "target": target}
                for entry, target in zip(data, targets, strict=True)
            ],
            "factTitle": _("Fact"),
            "max_category_len": max(map(len, categories), default=0),
        }

    @staticmethod
    def _upper_title(name: str) -> str:
        return (_("Savings") if name == SAVINGS else name).upper()

    def build_expenses(self) -> list[dict]:
        return [
            {"name": self._upper_title(entry["name"]), "y": entry["y"]}
            for entry in self._sort_chart_data(self.totals)
        ]

    def _sort_chart_data(self, data: dict) -> list[dict]:
        return sorted(
            [{"name": key, "y": val} for key, val in data.items()],
            key=itemgetter("y"),
            reverse=True,
        )


class InfoBuilder:
    @staticmethod
    def build(fact: InfoState, plan: InfoState) -> dict:
        delta = InfoState(
            income=fact.income - plan.income,
            saving=plan.saving - fact.saving,
            expense=plan.expense - fact.expense,
            per_day=plan.per_day - fact.per_day,
            balance=fact.balance - plan.balance,
        )

        return {"plan": asdict(plan), "fact": asdict(fact), "delta": asdict(delta)}
