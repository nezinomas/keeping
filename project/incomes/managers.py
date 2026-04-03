from django.db import models

from ..core.mixins.sum import SumMixin
from ..users.models import User


class IncomeTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)


class IncomeQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("account", "income_type").filter(
            income_type__journal=user.journal
        )