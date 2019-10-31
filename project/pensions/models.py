from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..accounts.models import Account
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract


class PensionType(TitleAbstract):
    class Meta:
        ordering = ['title']


class PensionQuerySet(SumMixin, models.QuerySet):
    def _related(self):
        return self.select_related('pension_type')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related().all()

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
                        default=0))
            )
            .values(
                's_past',
                's_now',
                title=models.F('pension_type__title'),
                id=models.F('pension_type__pk')
            )
        )


class Pension(models.Model):
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
