from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..users.models import User
from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract


class PensionTypeQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def items(self, year: int = None):
        return self.related()


class PensionType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pension_types'
    )

    # Managers
    objects = PensionTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['user', 'title']
        ordering = ['title']



class PensionQuerySet(SumMixin, models.QuerySet):
    def related(self):
        user = utils.get_user()
        qs = (
            self
            .select_related('pension_type')
            .filter(pension_type__user=user)
        )
        return qs

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related().all()

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                's_past': Decimal(),
                's_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('pension_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                s_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0)),
                s_fee_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='fee'),
                        default=0)),
                s_fee_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='fee'),
                        default=0))
            )
            .values(
                's_past',
                's_now',
                's_fee_now',
                's_fee_past',
                title=models.F('pension_type__title'),
                id=models.F('pension_type__pk')
            )
        )


class Pension(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-date', 'price']

    def __str__(self):
        return f'{(self.date)}: {self.pension_type}'

    # managers
    objects = PensionQuerySet.as_manager()

    def delete(self, *args, **kwargs):
        self.price = 0
        self.fee = 0

        super().delete(*args, **kwargs)


class PensionBalanceQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        qs = (
            self
            .select_related('pension_type')
            .filter(pension_type__user=user)
        )
        return qs

    def items(self):
        return self.related()

    def year(self, year: int):
        qs = self.related().filter(year=year)

        return qs.values(
            'year',
            'past_amount',
            'past_fee',
            'fees',
            'invested',
            'incomes',
            'market_value',
            'profit_incomes_proc',
            'profit_incomes_sum',
            'profit_invested_proc',
            'profit_invested_sum',
            title=F('pension_type__title')
        )


class PensionBalance(models.Model):
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE,
        related_name='pensions_balance'
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    past_amount = models.FloatField(default=0.0)
    past_fee = models.FloatField(default=0.0)
    fees = models.FloatField(default=0.0)
    invested = models.FloatField(default=0.0)
    incomes = models.FloatField(default=0.0)
    market_value = models.FloatField(default=0.0)
    profit_incomes_proc = models.FloatField(default=0.0)
    profit_incomes_sum = models.FloatField(default=0.0)
    profit_invested_proc = models.FloatField(default=0.0)
    profit_invested_sum = models.FloatField(default=0.0)

    # Managers
    objects = PensionBalanceQuerySet.as_manager()

    def __str__(self):
        return f'{self.pension_type.title}'
