from collections import defaultdict
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass, field
from typing import Any

from django.db.models import F, QuerySet, Sum
from django.utils.translation import gettext_lazy as _

from ...core.lib.table_columns import SAVINGS
from ...core.services.model_services import DatedModelService
from .. import models
from ..lib.month_states import MONTH_NUMS
from .plan_rows import PlanRow, PlanUrls


class PlanModelService(DatedModelService):
    urls: PlanUrls

    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects

    def generic_pivot_table(self, year: int, key_func: Callable[[Any], Hashable]):
        grouped = defaultdict(dict)
        # Meta.ordering sets the order of the table's rows
        for plan in self.year(year):
            grouped[key_func(plan)][plan.month] = plan.price

        return dict(grouped)

    def rows(self, year: int) -> list[PlanRow]:
        return [
            self._type_row(plan_type, months, year)
            for plan_type, months in self.pivot_table(year).items()
        ]

    def _type_row(self, plan_type, months: dict[int, int], year: int) -> PlanRow:
        return self.urls.row(plan_type, months, year, plan_type.pk)

    def summed_by_month(self, year):
        return (
            self.year(year)
            .order_by("month")
            .values("month")
            .annotate(amount=Sum("price", default=0))
            .values("month", "amount")
        )


class IncomePlanModelService(PlanModelService):
    urls = PlanUrls("plans:income_update", "plans:income_delete")

    def get_queryset(self):
        return models.IncomePlan.objects.select_related("income_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.income_type)


@dataclass
class ExpensePlanTables:
    necessary: list[PlanRow] = field(default_factory=list)
    everyday: list[PlanRow] = field(default_factory=list)


class ExpensePlanModelService(PlanModelService):
    urls = PlanUrls("plans:expense_update", "plans:expense_delete")

    def get_queryset(self):
        return models.ExpensePlan.objects.select_related("expense_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.expense_type)

    def row_tables(self, year: int) -> ExpensePlanTables:
        tables = ExpensePlanTables()
        for expense_type, months in self.pivot_table(year).items():
            table = tables.necessary if expense_type.necessary else tables.everyday
            table.append(self._type_row(expense_type, months, year))
        return tables

    def everyday_by_month(self, year: int):
        return self.summed_by_month(year).filter(expense_type__necessary=False)

    def necessary_by_month(self, year: int):
        return self.summed_by_month(year).filter(expense_type__necessary=True)


class SavingPlanModelService(PlanModelService):
    urls = PlanUrls("plans:saving_update", "plans:saving_delete")

    def get_queryset(self):
        return models.SavingPlan.objects.select_related("saving_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.saving_type)


class DayPlanModelService(PlanModelService):
    urls = PlanUrls("plans:day_update", "plans:day_delete")

    def get_queryset(self):
        return models.DayPlan.objects.filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda _plan: _("Daily"))

    def rows(self, year: int, states: dict[str, str]) -> list[PlanRow]:
        month_states = [states[month] for month in MONTH_NUMS]
        return [
            self.urls.row(title, months, year, states=month_states)
            for title, months in self.pivot_table(year).items()
        ]


class NecessaryPlanModelService(PlanModelService):
    urls = PlanUrls("plans:necessary_update", "plans:necessary_delete")

    def get_queryset(self):
        return models.NecessaryPlan.objects.select_related("expense_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(
            year, lambda plan: (plan.expense_type, plan.title)
        )

    def rows(self, year: int) -> list[PlanRow]:
        return [
            self.urls.row(
                f"{title} ({expense_type.title})",
                months,
                year,
                expense_type.pk,
                title,
            )
            for (expense_type, title), months in self.pivot_table(year).items()
        ]


@dataclass
class MonthTargets:
    """What the plans set for each Expense type, and for savings, in one month."""

    type_titles: Sequence[str]
    expense_plans: QuerySet
    necessary_plans: QuerySet
    saving_plans: QuerySet
    month: int

    @classmethod
    def for_month(
        cls,
        type_titles: Sequence[str],
        expense_plans: QuerySet,
        necessary_plans: QuerySet,
        saving_plans: QuerySet,
        month: int,
    ) -> dict[str, int]:
        return cls(
            type_titles, expense_plans, necessary_plans, saving_plans, month
        )._targets()

    def _targets(self) -> dict[str, int]:
        targets = dict.fromkeys(self.type_titles, 0)

        for plans in (self.expense_plans, self.necessary_plans):
            for title, total in self._totals_by_type_title(plans):
                if title in targets:
                    targets[title] += total

        targets[SAVINGS] = self.saving_plans.filter(month=self.month).aggregate(
            total=Sum("price", default=0)
        )["total"]

        return targets

    def _totals_by_type_title(self, plans: QuerySet):
        return (
            plans.filter(month=self.month)
            .values(type_title=F("expense_type__title"))
            .annotate(total=Sum("price", default=0))
            .values_list("type_title", "total")
        )
