from django.db import models

from ..core.models import TitleAbstract


class AccountQuerySet(models.QuerySet):
    pass


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=10
    )

    class Meta:
        ordering = ['order', 'title']

    # Managers
    objects = AccountQuerySet.as_manager()
