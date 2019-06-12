from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.models import TitleAbstract


class SavingTypeManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = self.get_queryset()

        return qs


class SavingType(TitleAbstract):
    objects = SavingTypeManager()

    class Meta:
        ordering = ['title']


class SavingManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = (
            self.get_queryset().
            prefetch_related('account', 'saving_type')
        )

        if 'year' in kwargs:
            year = kwargs['year']
            qs = qs.filter(date__year=year)

        return qs

    def past_items(self, *args, **kwargs):
        qs = (
            self.get_queryset().
            prefetch_related('account', 'saving_type')
        )

        if 'year' in kwargs:
            year = kwargs['year']
            qs = qs.filter(date__year__lte=year)

        return qs


class Saving(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE
    )

    objects = SavingManager()

    class Meta:
        ordering = ['-date', 'saving_type']

    def __str__(self):
        return str(self.saving_type)
