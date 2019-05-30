from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account


class TransactionManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = (
            self.get_queryset().
            prefetch_related('from_account', 'to_account')
        )

        if 'year' in kwargs:
            year = kwargs['year']
            qs = qs.filter(date__year=year)

        return qs


class Transaction(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='from_accounts'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='to_accounts'
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    objects = TransactionManager()

    class Meta:
        ordering = ['-date', 'amount', 'from_account']

    def __str__(self):
        return (
            '{} {}->{} {}'.
            format(self.date, self.from_account, self.to_account, self.amount)
        )
