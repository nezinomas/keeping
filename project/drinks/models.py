from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _l

from ..users.models import User
from .lib.drinks_options import DrinksOptions


class DrinkType(models.TextChoices):
    BEER = "beer", _l("Beer")
    WINE = "wine", _l("Wine")
    VODKA = "vodka", _l("Vodka")
    STDAV = "stdav", "Std Av"


class Drink(models.Model):
    date = models.DateField()
    stdav = models.FloatField(validators=[MinValueValidator(0.1)])
    option = models.CharField(
        max_length=7,
        choices=DrinkType.choices,
        default=DrinkType.BEER,
    )
    converted_from_ml = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        get_latest_by = ["date"]

    def __str__(self):
        msg = f"{self.date}, {self.option}, "
        if self.option == "stdav":
            stdav = str(self.stdav)
        else:
            ml = DrinksOptions(self.option).stdav_to_ml(self.stdav)
            stdav = f"{int(ml)}ml"

        return msg + stdav


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
        User, on_delete=models.CASCADE, related_name="drink_targets"
    )

    def __str__(self):
        ml = DrinksOptions(self.drink_type).stdav_to_ml(self.quantity)

        return f"{self.year}: {ml}"

    class Meta:
        ordering = ["-year"]
        unique_together = ["year", "user"]

    def save(self, *args, **kwargs):
        if self.drink_type != "stdav":
            self.quantity = DrinksOptions(self.drink_type).ml_to_stdav(
                self.quantity
            )

        super().save(*args, **kwargs)
