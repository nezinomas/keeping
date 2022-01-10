from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models

from ..users.models import User
from . import managers



class Counter(models.Model):
    date = models.DateField()
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)]
    )
    counter_type = models.CharField(
        max_length=254,
        blank=False,
        validators=[MinLengthValidator(3)]
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = managers.CounterQuerySet.as_manager()

    def __str__(self):
        return f'{self.date}: {self.quantity}'

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']