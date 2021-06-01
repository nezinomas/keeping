from datetime import date
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.mixins.from_db import MixinFromDbAccountId
from ..users.models import User
from . import managers


class Borrow(MixinFromDbAccountId):
    date = models.DateField()
    name = models.TextField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    returned = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = managers.BorrowQuerySet.as_manager()

    def __str__(self):
        return f'Pasiskolinta {round(self.price, 0)}'


class BorrowReturn(MixinFromDbAccountId):
    date = models.DateField(
        default=date.today,
        editable=False
    )
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

    def __str__(self):
        return f'Grąžinau {round(self.price, 1)}'

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            raise e

        obj = Borrow.objects.get(id=self.borrow_id)
        obj.returned += Decimal(self.price)
        obj.save()

    def delete(self, *args, **kwargs):
        try:
            super().delete(*args, **kwargs)
        except Exception as e:
            raise e

        obj = Borrow.objects.get(id=self.borrow_id)
        obj.returned -= Decimal(self.price)
        obj.save()


class Lent(MixinFromDbAccountId):
    date = models.DateField()
    name = models.TextField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    returned = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
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
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = managers.LentQuerySet.as_manager()

    def __str__(self):
        return f'Paskolinau {round(self.price, 1)}'


class LentReturn(MixinFromDbAccountId):
    date = models.DateField(
        default=date.today,
        editable=False
    )
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

    def __str__(self):
        return f'Grąžino {round(self.price, 1)}'

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            raise e

        obj = Lent.objects.get(id=self.lent_id)
        obj.returned += Decimal(self.price)
        obj.save()

    def delete(self, *args, **kwargs):
        try:
            super().delete(*args, **kwargs)
        except Exception as e:
            raise e

        obj = Lent.objects.get(id=self.lent_id)
        obj.returned -= Decimal(self.price)
        obj.save()
