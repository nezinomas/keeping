from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

from ..core.models import MonthAbstract
from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..journals.models import Journal
from ..savings.models import SavingType
from . import managers


class IncomePlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    income_type = models.ForeignKey(
        IncomeType,
        on_delete=models.CASCADE
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='income_plans'
    )

    objects = managers.YearManager('income_type')

    def __str__(self):
        return f'{self.year}/{self.income_type.title}'

    class Meta:
        ordering = ['income_type']
        unique_together = ('year', 'income_type', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(_('%(year)s year already has %(title)s plan.') % ({'year': self.year, 'title': self.income_type.title}))


class ExpensePlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    expense_type = models.ForeignKey(
        ExpenseType,
        on_delete=models.CASCADE
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='expense_plans'
    )

    objects = managers.YearManager('expense_type')

    def __str__(self):
        return f'{self.year}/{self.expense_type.title}'

    class Meta:
        ordering = ['expense_type']
        unique_together = ('year', 'expense_type', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(_('%(year)s year already has %(title)s plan.') % ({'year': self.year, 'title': self.expense_type.title}))


class SavingPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='saving_plans'
    )

    objects = managers.YearManager('saving_type')

    def __str__(self):
        return f'{self.year}/{self.saving_type.title}'

    class Meta:
        ordering = ['saving_type']
        unique_together = ('year', 'saving_type', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(_('%(year)s year already has %(title)s plan.') % ({'year': self.year, 'title': self.saving_type.title}))


class DayPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='day_plans'
    )

    objects = managers.YearManager()

    def __str__(self):
        return f'{self.year}'

    class Meta:
        ordering = ['year']
        unique_together = ('year', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            title = pgettext('plans day error', 'Day')
            raise ValidationError(_('%(year)s year already has %(title)s plan.') % ({'year': self.year, 'title': title}))


class NecessaryPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    title = models.CharField(max_length=100)
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='necessary_plans'
    )

    objects = managers.YearManager()

    def __str__(self):
        return f'{self.year}/{self.title}'

    class Meta:
        ordering = ['year', 'title']
        unique_together = ('year', 'title', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(_('%(year)s year already has %(title)s plan.') % ({'year': self.year, 'title': self.title}))
