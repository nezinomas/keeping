from django.db import models

from ..accounts.models import Account
from ..core.templatetags.cell_format import cellformat
from ..core.templatetags.math import price
from ..savings.models import SavingType


class Transaction(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions_from"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions_to"
    )
    price = models.PositiveIntegerField()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {cellformat(price(self.price))}"
        return f"{_from} -> {_to}"


class SavingClose(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_close_from"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="savings_close_to"
    )
    fee = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    price = models.PositiveIntegerField()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {cellformat(price(self.price))}"
        return f"{_from} -> {_to}"


class SavingChange(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_change_from"
    )
    to_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_change_to"
    )
    fee = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    price = models.PositiveIntegerField()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {cellformat(price(self.price))}"
        return f"{_from} -> {_to}"
