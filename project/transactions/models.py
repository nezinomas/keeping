from django.db import models
from django.utils.formats import number_format

from ..accounts.models import Account
from ..core.lib.convert_price import int_cents_to_float
from ..savings.models import SavingType


def money(cents: int) -> str:
    return number_format(int_cents_to_float(cents), 2, force_grouping=True)


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
        _to = f"{self.to_account}: {money(self.price)}"
        return f"{_from} -> {_to}"


class SavingClose(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_close_from"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="savings_close_to"
    )
    fee = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {money(self.price)}"
        return f"{_from} -> {_to}"


class SavingChange(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_change_from"
    )
    to_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_change_to"
    )
    fee = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {money(self.price)}"
        return f"{_from} -> {_to}"
