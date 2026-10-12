from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

from django.db.models import F, Sum
from django.utils.translation import gettext_lazy as _

from ...core.services.model_services import DatedModelService
from ...expenses.services.model_services import ExpenseTypeModelService
from .. import models


class PlanModelService(DatedModelService):
    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects

    @abstractmethod
    def pivot_table(self, year: int): ...

    def generic_pivot_table(self, year: int, key_func):
        grouped = defaultdict(dict)
        # Meta.ordering sets the order of the table's rows
        for plan in self.year(year):
            grouped[key_func(plan)][plan.month] = plan.price

        return dict(grouped)

    def summed_by_month(self, year):
        return (
            self.year(year)
            .order_by("month")
            .values("month")
            .annotate(amount=Sum("price", default=0))
            .values("month", "amount")
        )


class IncomePlanModelService(PlanModelService):
    def get_queryset(self):
        return models.IncomePlan.objects.select_related("income_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.income_type)


@dataclass
class ExpensePlanTables:
    necessary: dict = field(default_factory=dict)
    everyday: dict = field(default_factory=dict)


class ExpensePlanModelService(PlanModelService):
    def get_queryset(self):
        return models.ExpensePlan.objects.select_related("expense_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.expense_type)

    def pivot_tables(self, year: int) -> ExpensePlanTables:
        tables = ExpensePlanTables()
        for expense_type, months in self.pivot_table(year).items():
            table = tables.necessary if expense_type.necessary else tables.everyday
            table[expense_type] = months
        return tables

    def summed_by_month(self, year, necessary=False):
        return super().summed_by_month(year).filter(expense_type__necessary=necessary)


class SavingPlanModelService(PlanModelService):
    def get_queryset(self):
        return models.SavingPlan.objects.select_related("saving_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.saving_type)


class DayPlanModelService(PlanModelService):
    def get_queryset(self):
        return models.DayPlan.objects.filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda _plan: _("Daily"))


class NecessaryPlanModelService(PlanModelService):
    def get_queryset(self):
        return models.NecessaryPlan.objects.select_related("expense_type").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(
            year, lambda plan: (plan.expense_type, plan.title)
        )


class PlanAggregatorService:
    def __init__(self, user):
        self.user = user

    def get_monthly_plan_targets(self, year: int, month: int) -> dict:
        targets = self._initialize_targets()

        for service in (ExpensePlanModelService, NecessaryPlanModelService):
            self._add_type_plans(targets, service(self.user), year, month)
        self._add_saving_plans(targets, year, month)

        return targets

    def _initialize_targets(self) -> dict:
        expense_types = (
            ExpenseTypeModelService(self.user).items().values_list("title", flat=True)
        )
        targets = {title: 0 for title in expense_types}
        targets["savings"] = 0
        return targets

    @staticmethod
    def _add_type_plans(
        targets: dict,
        service: ExpensePlanModelService | NecessaryPlanModelService,
        year: int,
        month: int,
    ):
        rows = (
            service.year(year)
            .filter(month=month)
            .values(type_title=F("expense_type__title"))
            .annotate(total=Sum("price", default=0))
        )
        for row in rows:
            if row["type_title"] not in targets:
                continue
            targets[row["type_title"]] += row["total"]

    def _add_saving_plans(self, targets: dict, year: int, month: int):
        savings = (
            SavingPlanModelService(self.user)
            .year(year)
            .filter(month=month)
            .aggregate(total=Sum("price", default=0))
        )
        targets["savings"] += savings["total"]
