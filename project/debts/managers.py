from django.db import models

from ..core.mixins.sum import SumMixin
from ..users.models import User


class DebtQuerySet(models.QuerySet):
    def related(self, user: User, debt_type: str):
        return self.select_related("account", "journal").filter(
            journal=user.journal, debt_type=debt_type
        )

class DebtReturnQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User, debt_type: str):
        return self.select_related("account", "debt").filter(
            debt__journal=user.journal, debt__debt_type=debt_type
        )