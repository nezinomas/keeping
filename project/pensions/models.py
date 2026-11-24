from django.db import models

from ..core.models import TitleAbstract
from ..core.profit_balance import ProfitBalance
from ..journals.models import Journal


class PensionType(TitleAbstract):
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="pension_types"
    )
    created = models.DateTimeField(auto_now_add=True)
    closed = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["journal", "slug"], name="pensions_pensiontype_unique_slug"
            ),
        ]


class Pension(models.Model):
    date = models.DateField()
    price = models.PositiveIntegerField(default=0, blank=True)
    fee = models.PositiveIntegerField(default=0, blank=True)
    remark = models.TextField(max_length=1000, blank=True)
    pension_type = models.ForeignKey(PensionType, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date", "price"]

    def __str__(self):
        return f"{self.date}: {self.pension_type}"

    @property
    def journal(self):
        return self.pension_type.journal


class PensionBalance(ProfitBalance):
    owner_field = "pension_type"
    owner_closed_lookup = "pension_type__closed"

    pension_type = models.ForeignKey(
        PensionType, on_delete=models.CASCADE, related_name="pensions_balance"
    )

    class Meta:
        ordering = ["year", "pension_type__pk"]

    def __str__(self):
        return self.pension_type.title

    @property
    def owner(self) -> PensionType:
        return self.pension_type
