from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Max, Q

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
        qs = (
            self
            .related()
            .values('saving_type')
            .annotate(latest_date=Max('date'))
            .order_by()
        )

        q_statement = Q()
        for pair in qs:
            q_statement |= (Q(saving_type__exact=pair['saving_type']) & Q(date=pair['latest_date']))

        return qs.filter(q_statement).values(
                title=F('saving_type__title'),
                have=F('price'),
                latest_check=F('latest_date')
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
        qs = (
            self
            .related()
            .values('account')
            .annotate(latest_date=Max('date'))
            .order_by()
        )

        q_statement = Q()
        for pair in qs:
            q_statement |= (Q(account__exact=pair['account']) & Q(
                date=pair['latest_date']))

        return qs.filter(q_statement).values(
            title=F('account__title'),
            have=F('price'),
            latest_check=F('latest_date')
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
        qs = (
            self
            .related()
            .values('pension_type')
            .annotate(latest_date=Max('date'))
            .order_by()
        )

        q_statement = Q()
        for pair in qs:
            q_statement |= (Q(pension_type__exact=pair['pension_type']) & Q(
                date=pair['latest_date']))

        return qs.filter(q_statement).values(
            title=F('pension_type__title'),
            have=F('price'),
            latest_check=F('latest_date')
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
