from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .lib.db_sync import SAVING_FIELDS
from .mixins.shows_profit import ShowsProfitMixin


class FundBalance(ShowsProfitMixin, models.Model):
    """A Fund's balance row for a year: the Savings and the Pension funds keep one each.

    A subclass adds the Fund's foreign key and names it in `fund_field`, `fund` and
    `fund_closed_lookup`."""

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
