from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django_pandas.managers import DataFrameManager

from ..accounts.models import Account


class TransactionQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('from_account', 'to_account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()


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
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        ordering = ['-date', 'price', 'from_account']

    def __str__(self):
        return (
            '{} {}->{} {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = TransactionQuerySet.as_manager()
    pd = DataFrameManager()
