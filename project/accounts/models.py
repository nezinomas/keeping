from django.db import models

from ..core.models import TitleAbstract


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ['order', 'title']
