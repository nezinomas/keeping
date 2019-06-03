from django.core.validators import MinValueValidator
from django.db import models


class DrinkManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = self.get_queryset()

        if 'year' in kwargs:
            year = kwargs['year']
            qs = qs.filter(date__year=year)

        return qs


class Drink(models.Model):
    date = models.DateField()
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    objects = DrinkManager()
