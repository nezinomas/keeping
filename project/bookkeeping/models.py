from django.db import models

from ..accounts.models import Account
from ..core.services.signals_service import BalanceKind
from ..pensions.models import PensionType
from ..savings.models import SavingType


class SavingWorth(models.Model):
    fund_field = "saving_type"
    balance_kind = BalanceKind.SAVINGS

    date = models.DateTimeField()
    price = models.PositiveIntegerField()
    saving_type = models.ForeignKey(
        to=SavingType, on_delete=models.CASCADE, related_name="savings_worth"
    )

    class Meta:
        get_latest_by = ["date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date:%Y-%m-%d %H:%M} - {self.saving_type}"

    @property
    def journal(self):
        return self.saving_type.journal


class AccountWorth(models.Model):
    fund_field = "account"
    balance_kind = BalanceKind.ACCOUNTS

    date = models.DateTimeField()
    price = models.PositiveIntegerField()
    account = models.ForeignKey(
        to=Account, on_delete=models.CASCADE, related_name="accounts_worth"
    )

    class Meta:
        get_latest_by = ["date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date:%Y-%m-%d %H:%M} - {self.account}"

    @property
    def journal(self):
        return self.account.journal


class PensionWorth(models.Model):
    fund_field = "pension_type"
    balance_kind = BalanceKind.PENSIONS

    date = models.DateTimeField()
    price = models.PositiveIntegerField()
    pension_type = models.ForeignKey(
        to=PensionType, on_delete=models.CASCADE, related_name="pensions_worth"
    )

    class Meta:
        ordering = ["-date"]
        get_latest_by = ["date"]

    def __str__(self):
        return f"{self.date:%Y-%m-%d %H:%M} - {self.pension_type}"

    @property
    def journal(self):
        return self.pension_type.journal
