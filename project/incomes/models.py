from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.models import TitleAbstract


class IncomeType(TitleAbstract):
    class Meta:
        ordering = ['title']


class IncomeManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = (
            self.get_queryset().
            select_related('account')
            # prefetch_related('account')
        )

        if 'year' in kwargs:
            year = kwargs['year']
            qs = qs.filter(date__year=year)

        return qs


class Income(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE
    )
    income_type = models.ForeignKey(
        IncomeType,
        on_delete=models.CASCADE
    )

    objects = IncomeManager()

    class Meta:
        ordering = ['-date', 'price']

    def __str__(self):
        return str(self.date)
