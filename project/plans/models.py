from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from ..core.models import MonthAbstract
from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..savings.models import SavingType


class YearManager(models.Manager):
    def __init__(self, prefetch, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefetch = prefetch

    def year(self, year):
        qs = self.get_queryset().filter(year=year)

        if self._prefetch:
            qs = qs.select_related(self._prefetch)

        return qs

    def items(self, year):
        qs = self.get_queryset().all()

        if self._prefetch:
            qs = qs.select_related(self._prefetch)

        return qs


class PlanQuerySet(models.QuerySet):
    def __init__(self, prefetch, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefetch = prefetch

    def year(self, year):
        qs = self.filter(date__year=year)
        if self._prefetch:
            qs = qs.select_related(self._prefetch)

        return qs

    def items(self):
        return self.all()


class ExpensePlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    expense_type = models.ForeignKey(
        ExpenseType,
        on_delete=models.CASCADE
    )

    objects = YearManager('expense_type')

    class Meta:
        ordering = ['expense_type']
        unique_together = ('year', 'expense_type')


class SavingPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )

    objects = YearManager('saving_type')

    class Meta:
        ordering = ['saving_type']
        unique_together = ('year', 'saving_type')


class IncomePlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    income_type = models.ForeignKey(
        IncomeType,
        on_delete=models.CASCADE
    )

    objects = YearManager('income_type')

    class Meta:
        ordering = ['income_type']
        unique_together = ('year', 'income_type')


class DayPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
        unique=True
    )

    objects = YearManager(None)


class NecessaryPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    title = models.CharField(max_length=100)

    objects = YearManager(None)

    def __str__(self):
        return f'{self.year}/{self.title}'

    class Meta:
        unique_together = ('year', 'title')
