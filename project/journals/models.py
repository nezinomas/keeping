from datetime import date

from django.db import models

from ..core.models import TitleAbstract


class Journal(TitleAbstract):
    first_record = models.DateField(
        default=date.today,
        editable=False
    )
    unnecessary_expenses = models.CharField(
        max_length=254,
        null=True,
        blank=True
    )
    unnecessary_savings = models.BooleanField(
        default=False
    )
    lang = models.CharField(
        max_length=2,
        blank=False,
        default='en'
    )

    def __str__(self):
        return f'{self.title}'
