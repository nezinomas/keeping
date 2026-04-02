from django.db import models

from ..core.mixins.sum import SumMixin
from ..users.models import User


class SavingTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)


class SavingQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("account", "saving_type").filter(
            saving_type__journal=user.journal
        )


class SavingBalanceQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("saving_type").filter(
            saving_type__journal=user.journal
        )
