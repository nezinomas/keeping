from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.templatetags.math import price as convert_price
from ..journals.models import Journal
from . import managers


class Debt(models.Model):
    class DebtType(models.TextChoices):
        LEND = "lend", _("Lend")
        BORROW = "borrow", _("Borrow")

    date = models.DateField()
    debt_type = models.CharField(
        max_length=12,
        choices=DebtType.choices,
        default=DebtType.LEND,
    )
    name = models.CharField(max_length=100, validators=[MinLengthValidator(3)])
    price = models.PositiveIntegerField()
    returned = models.PositiveIntegerField(
        null=True,
        default=0,
    )
    closed = models.BooleanField(default=False)
    remark = models.TextField(max_length=500, blank=True)
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="debt_from_account"
    )
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)

    objects = managers.DebtQuerySet.as_manager()

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return str(self.name)


class DebtReturn(models.Model):
    date = models.DateField()
    price = models.PositiveIntegerField()
    remark = models.TextField(max_length=500, blank=True)
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="debt_return_account"
    )
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE)

    objects = managers.DebtReturnQuerySet.as_manager()

    class Meta:
        ordering = ["-debt__date", "debt__name", "-date"]

    def __str__(self):
        price = round(self.price, 1)

        text = ""
        if self.debt.debt_type == "lend":
            text = f"{_('Lend return')} {convert_price(price)}"

        if self.debt.debt_type == "borrow":
            text = f"{_('Borrow return')} {convert_price(price)}"

        return text
