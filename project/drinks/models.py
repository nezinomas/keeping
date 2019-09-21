from django.core.validators import MinValueValidator
from django.db import models


class DrinkQuerySet(models.QuerySet):
    def year(self, year):
        return self.filter(date__year=year)

    def items(self):
        return self.all()


class Drink(models.Model):
    date = models.DateField()
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    objects = DrinkQuerySet.as_manager()
