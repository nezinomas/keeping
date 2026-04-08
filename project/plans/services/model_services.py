from django.db.models import Q, Sum, Count
from collections import defaultdict
from ...core.services.model_services import BaseModelService
from .. import models


class CommonMethodsMixin:
    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects

    def generic_pivot_table(self, year: int, key_func):
        """
        INTERNAL METHOD: Groups tall database rows into a nested dictionary.
        `key_func` defines what object/value becomes the dictionary key.
        """
        # We rely on the model's Meta.ordering to sort the queryset properly
        qs = self.year(year)

        grouped = defaultdict(dict)
        for plan in qs:
            # Dynamically extract the object/tuple using the provided function
            group_key = key_func(plan)
            grouped[group_key][plan.month] = plan.price

        return dict(grouped)


class IncomePlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.IncomePlan.objects.select_related(
            "journal", "income_type"
        ).filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.income_type)
    

class ExpensePlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.ExpensePlan.objects.select_related(
            "journal", "expense_type"
        ).filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.expense_type)


class SavingPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.SavingPlan.objects.select_related(
            "journal", "saving_type"
        ).filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.saving_type)


class DayPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.DayPlan.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, ["year"])


class NecessaryPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.NecessaryPlan.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, ["expense_type__title", "title"])
