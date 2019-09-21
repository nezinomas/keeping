from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F

from ..accounts.models import Account
from ..core.mixins.queryset_balance import QuerySetBalanceMixin
from ..core.models import TitleAbstract


class SavingTypeQuerySet(QuerySetBalanceMixin, models.QuerySet):
    def incomes(self, year):
        return self.annotate_(year, 'saving', 'i')

    def fees(self, year):
        return self.annotate_(year, 'saving', 'f', 'fee')

    def savings_change_to(self, year):
        return self.annotate_(year, 'savings_change_to', 'change_to')

    def savings_change_to_fee(self, year):
        return self.annotate_(year, 'savings_change_to', 'change_to_fee', 'fee')

    def savings_change_from(self, year):
        return self.annotate_(year, 'savings_change_from', 'change_from')

    def savings_change_from_fee(self, year):
        return self.annotate_(year, 'savings_change_from', 'change_from_fee', 'fee')

    def savings_close_from(self, year):
        return self.annotate_(year, 'savings_close_from', 'close_from')

    def balance_year(self, year):
        return (
            self
            .annotate(a=Count('title', distinct=True))
            .values('id')
            .values(title=F('title'))
            .incomes(year)
            .fees(year)
            .savings_change_to(year)
            .savings_change_to_fee(year)
            .savings_change_from(year)
            .savings_change_from_fee(year)
            .savings_close_from(year)
            .annotate(past_amount=(
                0
                + F('i_past')
                + F('change_to_past')
                - F('change_from_past')
                - F('close_from_past')
            ))
            .annotate(past_fee=(
                0
                + F('f_past')
                + F('change_to_fee_past')
                + F('change_from_fee_past')
            ))
            .annotate(incomes=(
                0
                + F('i_now')
                + F('past_amount')
                + F('change_to_now')
                - F('change_from_now')
                - F('close_from_now')
            ))
            .annotate(fees=(
                0
                + F('f_now')
                + F('past_fee')
                + F('change_to_fee_now')
                + F('change_from_fee_now')
            ))
            .annotate(invested=(
                F('incomes') - F('fees')
            ))
            .values('title', 'incomes', 'past_amount', 'past_fee', 'fees', 'invested')
        )


class SavingType(TitleAbstract):
    class Meta:
        ordering = ['title']

    # Managers
    objects = SavingTypeQuerySet.as_manager()


class SavingQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('account', 'saving_type')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()


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
        on_delete=models.CASCADE,
        related_name='savings'
    )

    class Meta:
        ordering = ['-date', 'saving_type']

    def __str__(self):
        return str(self.saving_type)

    # Managers
    objects = SavingQuerySet.as_manager()
