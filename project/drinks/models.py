from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from ..counters.models import Counter
from ..users.models import User
from . import managers

MAX_BOTTLES = 20


class Drink(Counter):
    objects = managers.DrinkQuerySet.as_manager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        if self.quantity > MAX_BOTTLES:
            self.quantity = round(self.quantity / 500, 2)

        super().save(*args, **kwargs)


class DrinkTarget(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drink_targets'
    )

    objects = managers.DrinkTargetQuerySet.as_manager()

    def __str__(self):
        return f'{self.year}: {self.quantity}'

    class Meta:
        ordering = ['-year']
        unique_together = ['year', 'user']
