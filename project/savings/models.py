from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.models import TitleAbstract
from ..journals.models import Journal
from . import managers


class SavingType(TitleAbstract):
    class Types(models.TextChoices):
        SHARES = "shares", _("Shares")
        FUNDS = "funds", _("Funds")
        PENSIONS = "pensions", _("Pensions")

    created = models.DateTimeField(auto_now_add=True)
    closed = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="saving_types"
    )
    type = models.CharField(
        max_length=12,
        choices=Types.choices,
        default=Types.FUNDS,
    )

    # Managers
    objects = managers.SavingTypeQuerySet.as_manager()

    class Meta:
        unique_together = ["journal", "title"]
        ordering = ["type", "title"]

    def get_absolute_url(self):
        return reverse_lazy("savings:type_update", kwargs={"pk": self.pk})


class Saving(models.Model):
    date = models.DateField()
    price = models.PositiveIntegerField(null=True, blank=True)
    fee = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    remark = models.TextField(max_length=1000, blank=True)
    saving_type = models.ForeignKey(SavingType, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="savings"
    )

    # Managers
    objects = managers.SavingQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "saving_type"]
        indexes = [
            models.Index(fields=["account", "saving_type"]),
            models.Index(fields=["saving_type"]),
        ]

    def __str__(self):
        return f"{self.date}: {self.saving_type}"

    def get_absolute_url(self):
        return reverse_lazy("savings:update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("savings:delete", kwargs={"pk": self.pk})


class SavingBalance(models.Model):
    saving_type = models.ForeignKey(
        SavingType, on_delete=models.CASCADE, related_name="savings_balance"
    )
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

    # Managers
    objects = managers.SavingBalanceQuerySet.as_manager()

    def __str__(self):
        return f"{self.saving_type.title}"
