from django.db import models
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.models import TitleAbstract
from ..core.profit_balance import ProfitBalance
from ..core.validators import TITLE_VALIDATORS
from ..journals.models import Journal


class SavingType(TitleAbstract):
    class Types(models.TextChoices):
        SHARES = "shares", _("Shares")
        FUNDS = "funds", _("Funds")
        PENSIONS = "pensions", _("Pensions")

    class FeeSource(models.TextChoices):
        INVESTMENT = "investment", _("from the investment")
        ACCOUNT = "account", _("from the account")

    title = models.CharField(max_length=50, blank=False, validators=TITLE_VALIDATORS)
    slug = models.SlugField(editable=False, max_length=title.max_length)
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
    fee_source = models.CharField(
        max_length=12,
        choices=FeeSource.choices,
        default=FeeSource.INVESTMENT,
    )

    class Meta:
        ordering = ["type", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["journal", "slug"], name="savings_savingtype_unique_slug"
            ),
        ]


class Saving(models.Model):
    date = models.DateField()
    price = models.PositiveIntegerField(default=0, blank=True)
    fee = models.PositiveIntegerField(default=0, blank=True)
    remark = models.TextField(max_length=1000, blank=True)
    saving_type = models.ForeignKey(SavingType, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="savings"
    )

    class Meta:
        ordering = ["-date", "saving_type"]
        indexes = [
            models.Index(fields=["account", "saving_type"]),
            models.Index(fields=["saving_type"]),
        ]

    def __str__(self):
        return f"{self.date}: {self.saving_type}"

    @property
    def journal(self):
        return self.saving_type.journal


class SavingBalance(ProfitBalance):
    owner_field = "saving_type"
    owner_closed_lookup = "saving_type__closed"

    saving_type = models.ForeignKey(
        SavingType, on_delete=models.CASCADE, related_name="savings_balance"
    )

    class Meta:
        ordering = ["year", "saving_type__pk"]

    def __str__(self):
        return self.saving_type.title

    @property
    def owner(self) -> SavingType:
        return self.saving_type
