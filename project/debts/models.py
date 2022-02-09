from decimal import Decimal

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.mixins.old_values import OldValuesMixin
from ..journals.models import Journal
from . import managers


class Borrow(OldValuesMixin, models.Model):
    date = models.DateField()
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
        default=0
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
        related_name='borrow_to'
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE
    )

    objects = managers.BorrowQuerySet.as_manager()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return str(self.name)


class BorrowReturn(OldValuesMixin, models.Model):
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
        related_name='borrow_from'
    )
    borrow = models.ForeignKey(
        Borrow,
        on_delete=models.CASCADE
    )

    objects = managers.BorrowReturnQuerySet.as_manager()

    class Meta:
        ordering = ['borrow__closed', 'borrow__name', '-date']

    def __str__(self):
        return f'Grąžinau {round(self.price, 1)}'

    def save(self, *args, **kwargs):
        obj = Borrow.objects.get(id=self.borrow_id)
        obj.returned = obj.returned if obj.returned else Decimal('0')

        if not self.pk:
            obj.returned += Decimal(self.price)
        else:
            old = BorrowReturn.objects.get(pk=self.pk)
            dif = self.price - old.price
            obj.returned += dif

        if obj.price == obj.returned:
            obj.closed = True

        obj.save()

        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        try:
            super().delete(*args, **kwargs)
        except Exception as e:
            raise e

        obj = Borrow.objects.get(id=self.borrow_id)
        obj.returned -= Decimal(self.price)
        obj.save()


class Lent(OldValuesMixin, models.Model):
    date = models.DateField()
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
        related_name='lent_from_account'
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE
    )

    objects = managers.LentQuerySet.as_manager()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return str(self.name)


class LentReturn(OldValuesMixin, models.Model):
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
        related_name='lent_return_account'
    )
    lent = models.ForeignKey(
        Lent,
        on_delete=models.CASCADE
    )

    objects = managers.LentReturnQuerySet.as_manager()

    class Meta:
        ordering = ['lent__closed', 'lent__name', '-date']

    def __str__(self):
        return f'Grąžino {round(self.price, 1)}'

    def save(self, *args, **kwargs):
        obj = Lent.objects.get(id=self.lent_id)
        obj.returned = obj.returned if obj.returned else Decimal('0')

        if not self.pk:
            obj.returned += Decimal(self.price)
        else:
            old =LentReturn.objects.get(pk=self.pk)
            dif = self.price - old.price
            obj.returned += dif

        if obj.price == obj.returned:
            obj.closed = True

        obj.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            super().delete(*args, **kwargs)
        except Exception as e:
            raise e

        obj = Lent.objects.get(id=self.lent_id)
        obj.returned -= Decimal(self.price)
        obj.save()
