from django.db import models
from django.utils.translation import gettext_lazy as _l


class DrinkType(models.TextChoices):
    BEER = "beer", _l("Beer")
    WINE = "wine", _l("Wine")
    VODKA = "vodka", _l("Vodka")
    STDAV = "stdav", "Std Av"
