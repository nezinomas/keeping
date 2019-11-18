from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Max

from ..accounts.models import Account
from ..core.lib import utils
from ..pensions.models import PensionType
from ..savings.models import SavingType


# ----------------------------------------------------------------------------
#                                                                  SavingWorth
# ----------------------------------------------------------------------------
class SavingWorthQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('saving_type')
            .filter(saving_type__user=user)
        )

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
        validators=[MinValueValidator(Decimal('0.0'))]
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


# ----------------------------------------------------------------------------
#                                                                 AccountWorth
# ----------------------------------------------------------------------------
class AccountWorthQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('account')
            .filter(account__user=user)
        )

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
        validators=[MinValueValidator(Decimal('0.0'))]
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

    # Managers
    objects = AccountWorthQuerySet.as_manager()


# ----------------------------------------------------------------------------
#                                                                  PensionWorth
# ----------------------------------------------------------------------------
class PensionWorthQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('pension_type')
            .filter(pension_type__user=user)
        )

    def items(self):
        return (
            self
            .related()
            .annotate(max_date=Max('pension_type__pensions_worth__date'))
            .filter(date=F('max_date'))
            .values(title=F('pension_type__title'), have=F('price'))
        )


class PensionWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE,
        related_name='pensions_worth'
    )

    class Meta:
        get_latest_by = ['date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.pension_type}'

    # Managers
    objects = PensionWorthQuerySet.as_manager()
