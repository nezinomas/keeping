from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _l

from ..users.models import User
from .lib.drink_quantity import DrinkQuantity


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

    @property
    def amount(self) -> DrinkQuantity:
        return DrinkQuantity.from_stdav(
            self.stdav, self.option, is_volume=self.converted_from_ml
        )

    def __str__(self):
        # always names the volume, even for a record entered as a count
        volume = DrinkQuantity.from_stdav(self.stdav, self.option, is_volume=True)
        shown = f"{int(volume.value)}ml" if volume.is_volume else str(volume.stdav)

        return f"{self.date}, {self.option}, {shown}"


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

    @property
    def amount(self) -> DrinkQuantity:
        """The volume the user typed, in the drink type they chose at the time.

        Not the same reading as `DrinkTargetDTO.amount`, which re-expresses the
        target in whichever drink type the user is currently viewing in.
        """
        return DrinkQuantity.from_stdav(self.quantity, self.drink_type, is_volume=True)

    def __str__(self):
        return f"{self.year}: {self.amount.value}"

    class Meta:
        ordering = ["-year"]
        unique_together = ["year", "user"]

    def save(self, *args, **kwargs):
        self.quantity = DrinkQuantity.from_volume(self.quantity, self.drink_type).stdav

        super().save(*args, **kwargs)
