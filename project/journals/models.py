from datetime import date

from django.db import models

from ..core.models import TitleAbstract


class Journal(TitleAbstract):
    first_record = models.DateField(
        default=date.today,
        editable=False
    )

    def __str__(self):
        return f'{self.title}'
