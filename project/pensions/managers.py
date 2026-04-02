from django.db import models

from ..core.mixins.sum import SumMixin
from ..users.models import User


class PensionTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)


class PensionQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("pension_type").filter(
            pension_type__journal=user.journal
        )

class PensionBalanceQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("pension_type").filter(
            pension_type__journal=user.journal
        )
