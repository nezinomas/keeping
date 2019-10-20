from django.db import models

from ..core.models import TitleAbstract


class AccountQuerySet(models.QuerySet):
    def items(self, year: int = None):
        return self


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=10
    )

    class Meta:
        ordering = ['order', 'title']

    # Managers
    objects = AccountQuerySet.as_manager()
