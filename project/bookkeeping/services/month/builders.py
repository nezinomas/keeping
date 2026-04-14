from dataclasses import asdict
from functools import cached_property
from operator import itemgetter

import polars as pl
from django.utils.translation import gettext as _

from .dtos import InfoState


class MonthTableBuilder:
    """
    Merges expenses and savings into a single Polars DataFrame representing the month
    """

    def __init__(self, expense_df: pl.DataFrame, saving_df: pl.DataFrame):
        self.df = self._build_table(expense_df, saving_df)

    def _build_table(
        self, expense_df: pl.DataFrame, saving_df: pl.DataFrame
    ) -> pl.DataFrame:
        # If exists at least two columns (date + at least one expense type)
        # create total column
        if expense_df.shape[1] > 1:
            expense_df = expense_df.with_columns(
                pl.sum_horizontal(pl.exclude("date")).alias(_("Total"))
            )

        return expense_df.join(
            saving_df, on="date", how="full", coalesce=True, nulls_equal=True
        )

    @cached_property
    def table(self) -> list[dict]:
        return [] if self.df.is_empty() else self.df.to_dicts()

    @cached_property
    def total_row(self) -> dict:
        if self.df.is_empty() or self.df.shape[1] == 1:
            return {}
        return self.df.select(pl.exclude("date")).sum().to_dicts()[0]


class ChartBuilder:
    """Formats financial data specifically for frontend charts."""

    def __init__(self, targets: dict, totals: dict):
        self.totals = {k: v for k, v in totals.items() if k != _("Total")}
        self.targets = targets

    def build_targets(self) -> dict:
        data = self._sort_chart_data(self.totals)

        categories, data_target, data_fact, category_len = [], [], [], []

        for entry in data:
            name = entry["name"]
            target = self.targets.get(name, 0)

            categories.append(name.upper())
            data_target.append(target)
            data_fact.append({"y": entry["y"], "target": target})

            category_len.append(len(name))

        return {
            "categories": categories,
            "target": data_target,
            "targetTitle": _("Plan"),
            "fact": data_fact,
            "factTitle": _("Fact"),
            "max_category_len": max((len(c) for c in categories), default=0),
            "category_len": len(categories),
        }

    def build_expenses(self) -> list[dict]:
        data = self._sort_chart_data(self.totals)
        for entry in data:
            entry["name"] = entry["name"].upper()
        return data

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
