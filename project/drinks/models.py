from django.core.validators import MinValueValidator
from django.db import models


class DrinkManager(models.Manager):
    def items(self, year):
        return self.get_queryset().filter(date__year=year)


class Drink(models.Model):
    date = models.DateField()
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    objects = DrinkManager()
