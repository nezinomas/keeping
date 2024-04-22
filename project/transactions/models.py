from django.db import models
from django.urls import reverse_lazy

from ..accounts.models import Account
from ..core.templatetags.math import price
from ..core.templatetags.cell_format import cellformat
from ..savings.models import SavingType
from . import managers


class Transaction(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions_from"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions_to"
    )
    price = models.PositiveIntegerField()

    objects = managers.TransactionQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        return f"{self.date} {self.from_account} -> {self.to_account}: {cellformat(price(self.price))}"

    def get_absolute_url(self):
        return reverse_lazy("transactions:update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("transactions:delete", kwargs={"pk": self.pk})


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

    objects = managers.SavingCloseQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        return f"{self.date} {self.from_account} -> {self.to_account}: {cellformat(price(self.price))}"

    def get_absolute_url(self):
        return reverse_lazy("transactions:savings_close_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("transactions:savings_close_delete", kwargs={"pk": self.pk})


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

    objects = managers.SavingChangeQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "price", "from_account"]
        indexes = [
            models.Index(fields=["from_account"]),
            models.Index(fields=["to_account"]),
        ]

    def __str__(self):
        return f"{self.date} {self.from_account} -> {self.to_account}: {cellformat(price(self.price))}"

    def get_absolute_url(self):
        return reverse_lazy(
            "transactions:savings_change_update", kwargs={"pk": self.pk}
        )

    def get_delete_url(self):
        return reverse_lazy(
            "transactions:savings_change_delete", kwargs={"pk": self.pk}
        )
