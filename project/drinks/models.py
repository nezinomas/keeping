from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from ..users.models import User
from . import managers
from .lib.drinks_options import DrinksOptions

MAX_BOTTLES = 20


class DrinkType(models.TextChoices):
    BEER = 'beer', _l('Beer')
    WINE = 'wine', _l('Wine')
    VODKA = 'vodka', _l('Vodka')
    STDAV = 'stdav', 'Std Av'


class Drink(models.Model):
    date = models.DateField()
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)]
    )
    option = models.CharField(
        max_length=7,
        choices=DrinkType.choices,
        default=DrinkType.BEER,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = managers.DrinkQuerySet.as_manager()

    def __str__(self):
        qty = DrinksOptions().ratio
        return f'{self.date}: {round(self.quantity * qty, 2)}'

    def save(self, *args, **kwargs):
        obj = DrinksOptions(drink_type=self.option)

        if self.quantity > MAX_BOTTLES:
            q = obj.ml_to_stdav(drink_type=self.option, ml=self.quantity)
        else:
            q = self.quantity / obj.ratio

        self.quantity = q

        super().save(*args, **kwargs)


class DrinkTarget(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    quantity = models.FloatField()
    drink_type = models.CharField(
        max_length=7,
        choices=DrinkType.choices,
        default=DrinkType.BEER,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drink_targets'
    )

    objects = managers.DrinkTargetQuerySet.as_manager()

    def __str__(self):
        obj = DrinksOptions()
        ml = obj.stdav_to_ml(drink_type=self.drink_type, stdav=self.quantity)

        return f'{self.year}: {ml}'

    class Meta:
        ordering = ['-year']
        unique_together = ['year', 'user']

    def save(self, *args, **kwargs):
        if self.drink_type != 'stdav':
            obj = DrinksOptions()
            self.quantity = obj.ml_to_stdav(drink_type=self.drink_type, ml=self.quantity)

        super().save(*args, **kwargs)
