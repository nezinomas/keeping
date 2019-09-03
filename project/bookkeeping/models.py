from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Max

from ..accounts.models import Account
from ..savings.models import SavingType


#
# Savings Worth
#
class SavingWorthQuerySet(models.QuerySet):
    def related(self):
        return self.select_related('saving_type')

    def items(self):
        return self.related().annotate(
            max_date=Max('saving_type__savingworth__date')
        ).filter(
            date=F('max_date')
        )


class SavingWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )

    class Meta:
        get_latest_by = ['date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.saving_type}'

    # Managers
    objects = SavingWorthQuerySet.as_manager()


#
# Accounts Worth
#
class AccountWorthQuerySet(models.QuerySet):
    def related(self):
        return self.select_related('account')

    def items(self):
        return self.related().annotate(
            max_date=Max('account__accountworth__date')
        ).filter(
            date=F('max_date')
        )


class AccountWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE
    )

    class Meta:
        get_latest_by = ['date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.account}'

    # Managers
    objects = AccountWorthQuerySet.as_manager()
