from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .lib.db_sync import SAVING_FIELDS
from .mixins.shows_profit import ShowsProfitMixin


class ProfitBalance(ShowsProfitMixin, models.Model):
    """An Owner's balance row for a year that can show a profit: a Fund's
    (`SavingBalance`) or a Pension fund's (`PensionBalance`).

    A subclass adds the Owner's foreign key, names it in `owner_field`, returns the
    Owner from `owner` and names its closing year's lookup in `owner_closed_lookup`."""

    owner_field: str
    sync_fields = SAVING_FIELDS

    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    latest_check = models.DateTimeField(null=True, blank=True)
    past_amount = models.IntegerField(default=0)
    past_fee = models.IntegerField(default=0)
    fee = models.IntegerField(default=0)
    per_year_incomes = models.IntegerField(default=0)
    per_year_fee = models.IntegerField(default=0)
    sold = models.IntegerField(default=0)
    sold_fee = models.IntegerField(default=0)
    incomes = models.IntegerField(default=0)
    market_value = models.IntegerField(default=0)
    profit_sum = models.IntegerField(default=0)
    profit_proc = models.FloatField(default=0.0)
    sold_since_check = models.IntegerField(default=0)

    class Meta:
        abstract = True
