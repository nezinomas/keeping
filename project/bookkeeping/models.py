from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Max

from ..accounts.models import Account
from ..core.lib.post_save import post_save_account_stats
from ..savings.models import SavingType


#
# Savings Worth
#
class SavingWorthQuerySet(models.QuerySet):
    def related(self):
        return self.select_related('saving_type')

    def items(self):
        return (
            self
            .related()
            .annotate(max_date=Max('saving_type__savings_worth__date'))
            .filter(date=F('max_date'))
            .values(title=F('saving_type__title'), have=F('price'))
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
        on_delete=models.CASCADE,
        related_name='savings_worth'
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
        return (
            self.related()
            .annotate(max_date=Max('account__accounts_worth__date'))
            .filter(date=F('max_date'))
            .values('id')
            # extra groupby with unique model field, because
            # keyword 'account' conflicts with model account field
            .values(title=F('account__title'), have=F('price'))
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
        on_delete=models.CASCADE,
        related_name='accounts_worth'
    )

    class Meta:
        get_latest_by = ['date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.account}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        post_save_account_stats(self.account.id)

    # Managers
    objects = AccountWorthQuerySet.as_manager()
