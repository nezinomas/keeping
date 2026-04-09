from collections import defaultdict

from django.db.models import Count, F, Sum

from ...core.services.model_services import BaseModelService
from ...expenses.services.model_services import ExpenseTypeModelService
from .. import models
from django.utils.translation import gettext_lazy as _

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
        # Rely on the model's Meta.ordering to sort the queryset properly
        qs = self.year(year)

        grouped = defaultdict(dict)
        for plan in qs:
            # Dynamically extract the object/tuple using the provided function
            group_key = key_func(plan)
            grouped[group_key][plan.month] = plan.price

        return dict(grouped)

    def generic_summed_by_month(self, year, group_by):
        return (
            self.year(year)
            .annotate(cnt=Count(group_by))
            .values("cnt")
            .annotate(amount=Sum("price", default=0))
            .values("month", "amount")
        )


    def get_monthly_plan_targets(self, year: int, month: int) -> dict:
        expense_types = (
            ExpenseTypeModelService(self.user).items().values_list("title", flat=True)
        )
        targets = {title: 0 for title in expense_types}

        # Pre-fill Savings
        savings_title = _("Savings")
        targets[savings_title] = 0

        # 2. Get Expenses (Grouped & Summed)
        expenses = (
            ExpensePlanModelService(self.user)
            .year(year)
            .filter(month=month)
            .values(type_title=F("expense_type__title"))
            .annotate(total=Sum("price", default=0))
        )
        for row in expenses:
            if row["type_title"] in targets:
                targets[row["type_title"]] += row["total"]

        # 3. Get Necessary (Grouped & Summed)
        necessary = (
            NecessaryPlanModelService(self.user)
            .year(year)
            .filter(month=month)
            .values(type_title=F("expense_type__title"))
            .annotate(total=Sum("price", default=0))
        )
        for row in necessary:
            if row["type_title"] in targets:
                targets[row["type_title"]] += row["total"]

        # 4. Get Savings
        savings = (
            SavingPlanModelService(self.user)
            .year(year)
            .filter(month=month)
            .aggregate(total=Sum("price", default=0))
        )
        if savings.get("total"):
            targets[savings_title] += savings["total"]

        return targets


class IncomePlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.IncomePlan.objects.select_related(
            "journal", "income_type"
        ).filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.income_type)

    def summed_by_month(self, year):
        return self.generic_summed_by_month(year, "income_type")


class ExpensePlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.ExpensePlan.objects.select_related(
            "journal", "expense_type"
        ).filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.expense_type)

    def summed_by_month(self, year, necessary=False):
        return self.generic_summed_by_month(year, "expense_type").filter(
            expense_type__necessary=necessary
        )


class SavingPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.SavingPlan.objects.select_related(
            "journal", "saving_type"
        ).filter(journal=self.user.journal)

    def pivot_table(self, year: int):
        return self.generic_pivot_table(year, lambda plan: plan.saving_type)

    def summed_by_month(self, year):
        return self.generic_summed_by_month(year, "saving_type")


class DayPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.DayPlan.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        qs = self.generic_pivot_table(year, lambda plan: plan.year)
        return qs[year] if qs else {}

    def summed_by_month(self, year):
        return self.generic_summed_by_month(year, "id")


class NecessaryPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.NecessaryPlan.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def pivot_table(self, year: int):
        return self.generic_pivot_table(
            year, lambda plan: (plan.expense_type, plan.title)
        )

    def summed_by_month(self, year):
        return self.generic_summed_by_month(year, ["expense_type", "title"])
