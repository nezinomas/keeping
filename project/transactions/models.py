from django.db import models

from ..accounts.models import Account
from ..core.lib.money_cells import euros
from ..savings.models import SavingType
from .close_rules import KEEP, CloseRule, Removed


class Move(models.Model):
    """Each model declares its own two accounts: their targets and names differ."""

    date = models.DateField()
    price = models.PositiveIntegerField()

    from_account: models.ForeignKey
    to_account: models.ForeignKey

    class Meta:
        abstract = True
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        _from = f"{self.date} {self.from_account}"
        _to = f"{self.to_account}: {euros(self.price, '2g')}"
        return f"{_from} -> {_to}"

    @property
    def journal(self):
        return self.from_account.journal


class Transaction(Move):
    from_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions_from"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions_to"
    )


class FundMove(Move):
    """A move out of a fund; the receiver reads `close_rule` (the form's word) once,
    and `Removed` for the fund it was loaded from when it leaves it or is deleted."""

    fee = models.PositiveIntegerField(default=0)

    close_rule: CloseRule = KEEP
    # empty until the row is loaded or saved: a new move has left no fund
    removed: tuple[Removed, ...] = ()

    class Meta(Move.Meta):
        abstract = True

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


class SavingClose(FundMove):
    from_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_close_from"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="savings_close_to"
    )


class SavingChange(FundMove):
    from_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_change_from"
    )
    to_account = models.ForeignKey(
        SavingType, on_delete=models.PROTECT, related_name="savings_change_to"
    )
