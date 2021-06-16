from datetime import date

from django.db import models

from ..users.models import User
from . import managers


class Journal(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='journal'
    )
    year = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    month = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    first_record = models.DateField(
        default=date.today,
        editable=False
    )

    objects = managers.JournalQuerySet.as_manager()

    def __str__(self):
        return f'{self.user} Journal'
