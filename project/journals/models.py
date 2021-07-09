from datetime import date

from django.db import models

from ..core.models import TitleAbstract


class Journal(TitleAbstract):
    first_record = models.DateField(
        default=date.today,
        editable=False
    )
    not_use_expenses = models.CharField(
        max_length=254,
        null=True,
        blank=True
    )
    not_use_savings = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f'{self.title}'
