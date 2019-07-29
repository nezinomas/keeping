from django.db import models

from ..core.models import TitleAbstract


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=10
    )

    class Meta:
        ordering = ['order', 'title']
