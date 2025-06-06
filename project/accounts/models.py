from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse_lazy

from ..core.models import TitleAbstract
from ..journals.models import Journal
from . import managers


class Account(TitleAbstract):
    order = models.PositiveIntegerField(default=10)
    created = models.DateTimeField(auto_now_add=True)
    closed = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="accounts"
    )

    # Managers
    objects = managers.AccountQuerySet.as_manager()

    class Meta:
        unique_together = ["journal", "title"]
        ordering = ["order", "title"]

    def get_absolute_url(self):
        return reverse_lazy("accounts:update", kwargs={"pk": self.pk})


class AccountBalance(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="accounts_balance"
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    latest_check = models.DateTimeField(null=True, blank=True)
    past = models.IntegerField(default=0)
    incomes = models.IntegerField(default=0)
    expenses = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)
    have = models.IntegerField(default=0)
    delta = models.IntegerField(default=0)

    # Managers
    objects = managers.AccountBalanceQuerySet.as_manager()

    class Meta:
        ordering = ["year", "account__pk"]

    def __str__(self):
        return f"{self.account.title}"
