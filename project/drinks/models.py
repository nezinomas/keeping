from django.core.validators import MinValueValidator
from django.db import models


class Drink(models.Model):
    date = models.DateField()
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
