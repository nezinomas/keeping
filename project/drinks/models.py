from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from ..counters.models import Counter
from ..users.models import User
from . import managers
from .lib.drinks_options import DrinksOptions

MAX_BOTTLES = 20


class Drink(Counter):
    objects = managers.DrinkQuerySet.as_manager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        obj = DrinksOptions()

        if self.quantity > MAX_BOTTLES:
            q = obj.ml_to_stdav(drink_type=self.option, ml=self.quantity)
        else:
            q = self.quantity / obj.get_ratio(drink_type=self.option)

        self.quantity = q

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
