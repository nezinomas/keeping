from ...core.services.model_services import BaseModelService
from .. import models


class CommonMethodsMixin:
    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects


class IncomePlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.IncomePlan.objects.select_related(
            "journal", "income_type"
        ).filter(journal=self.user.journal)


class ExpensePlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.ExpensePlan.objects.select_related(
            "journal", "expense_type"
        ).filter(journal=self.user.journal)


class SavingPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.SavingPlan.objects.select_related(
            "journal", "saving_type"
        ).filter(journal=self.user.journal)


class DayPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.DayPlan.objects.select_related("journal").filter(
            journal=self.user.journal
        )


class NecessaryPlanModelService(CommonMethodsMixin, BaseModelService):
    def get_queryset(self):
        return models.NecessaryPlan.objects.select_related("journal").filter(
            journal=self.user.journal
        )
