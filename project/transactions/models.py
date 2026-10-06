from django.db import models
from django.utils.formats import number_format

from ..accounts.models import Account
from ..core.lib.convert_price import int_cents_to_float
from ..savings.models import SavingType
from .close_rules import KEEP, CloseBox, KeepClose


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


class FundMove:
    """A move out of a fund; the receiver reads `close_rule` (the form's word) once
    and follows `left_funds`, the fund the row was loaded from if it left it."""

    close_rule: KeepClose | CloseBox = KEEP
    _loaded_funds: tuple[int, ...] = ()

    @classmethod
    def from_db(cls, db, field_names, values, **kwargs):
        instance = super().from_db(db, field_names, values, **kwargs)
        # a deferred fund would cost a query per row; such a row is never saved
        if "from_account_id" in instance.__dict__:
            instance._loaded_funds = (instance.from_account_id,)

        return instance

    @property
    def left_funds(self) -> tuple[int, ...]:
        return tuple(f for f in self._loaded_funds if f != self.from_account_id)

    def settle(self) -> None:
        self.close_rule = KEEP
        self._loaded_funds = (self.from_account_id,)


class SavingClose(FundMove, models.Model):
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


class SavingChange(FundMove, models.Model):
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
