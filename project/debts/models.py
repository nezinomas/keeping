from decimal import Decimal

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.mixins.old_values import OldValuesMixin
from ..journals.models import Journal
from . import managers


class Debt(OldValuesMixin, models.Model):
    class Types(models.TextChoices):
        LEND = 'lend', _('Lend')
        BORROW = 'borrow', _('Borrow')

    date = models.DateField()
    type = models.CharField(
        max_length=12,
        choices=Types.choices,
        default=Types.LEND,
    )
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3)]
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    returned = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default=0,
    )
    closed = models.BooleanField(
        default=False
    )
    remark = models.TextField(
        max_length=500,
        blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='debt_from_account'
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE
    )

    objects = managers.DebtQuerySet.as_manager()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return str(self.name)


class DebtReturn(OldValuesMixin, models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    remark = models.TextField(
        max_length=500,
        blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='debt_return_account'
    )
    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE
    )

    objects = managers.DebtReturnQuerySet.as_manager()

    class Meta:
        ordering = ['debt__closed', 'debt__name', '-date']

    def __str__(self):
        _price = round(self.price, 1)
        if self.debt.type == 'lend':
            return f'{_("Lend return")} {_price}'

        if self.debt.type == 'borrow':
            return f'{_("Borrow return")} {_price}'


    def save(self, *args, **kwargs):
        qs = Debt.objects.filter(id=self.debt_id)
        obj = qs[0]

        _returned = obj.returned if obj.returned else Decimal('0')
        _closed = False

        if not self.pk:
            _returned += Decimal(self.price)
        else:
            old = DebtReturn.objects.get(pk=self.pk)
            dif = self.price - old.price
            _returned += dif

        if obj.price == _returned:
            _closed = True

        qs.update(returned=_returned, closed=_closed)

        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        try:
            super().delete(*args, **kwargs)
        except Exception as e:
            raise e

        qs = Debt.objects.filter(id=self.debt_id)
        _returned = qs[0].returned - Decimal(self.price)

        qs.update(returned=_returned)
