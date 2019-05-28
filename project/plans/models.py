from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from ..core.models import MonthAbstract
from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..savings.models import SavingType


class YearManager(models.Manager):
    def items(self, year):
        return self.get_queryset().filter(year=year)


class ExpensePlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2050)]
    )
    expense_type = models.ForeignKey(
        ExpenseType,
        on_delete=models.CASCADE
    )

    objects = YearManager()

    class Meta:
        ordering = ['expense_type']
        unique_together = ('year', 'expense_type')


class SavingPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2050)]
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )

    objects = YearManager()

    class Meta:
        ordering = ['saving_type']
        unique_together = ('year', 'saving_type')


class IncomePlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2050)]
    )
    income_type = models.ForeignKey(
        IncomeType,
        on_delete=models.CASCADE
    )

    objects = YearManager()

    class Meta:
        ordering = ['income_type']
        unique_together = ('year', 'income_type')


class DayPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2050)],
        unique=True
    )

    objects = YearManager()
