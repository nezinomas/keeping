from django.db import models
from django.utils.formats import number_format

from ..accounts.models import Account
from ..core.lib.convert_price import int_cents_to_float
from ..savings.models import SavingType
from .close_rules import KEEP, CloseRule, Removed


def money(cents: int) -> str:
    return number_format(int_cents_to_float(cents), 2, force_grouping=True)


class Move:
    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {money(self.price)}"
        return f"{_from} -> {_to}"

    @property
    def journal(self):
        return self.from_account.journal


class Transaction(Move, models.Model):
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


class FundMove(Move):
    """A move out of a fund; the receiver reads `close_rule` (the form's word) once,
    and `Removed` for the fund it was loaded from when it leaves it or is deleted."""

    close_rule: CloseRule = KEEP
    # empty until the row is loaded or saved: a new move has left no fund
    removed: tuple[Removed, ...] = ()

    @classmethod
    def from_db(cls, db, field_names, values, **kwargs):
        instance = super().from_db(db, field_names, values, **kwargs)
        # a deferred field would cost a query per row; such a row is never saved
        if {"from_account_id", "date"} <= instance.__dict__.keys():
            instance.settle()

        return instance

    @property
    def left_funds(self) -> tuple[Removed, ...]:
        return tuple(
            move for move in self.removed if move.fund_pk != self.from_account_id
        )

    def settle(self) -> None:
        self.close_rule = KEEP
        self.removed = (Removed(self.from_account_id, self.date),)


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
