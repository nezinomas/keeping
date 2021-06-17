from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from ..core.lib import utils
from ..core.models import MonthAbstract
from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..journals.models import Journal
from ..savings.models import SavingType


class YearManager(models.Manager):
    def __init__(self, prefetch=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefetch = prefetch

    def related(self):
        journal = utils.get_journal()
        related = ['journal']

        if self._prefetch:
            related.append(self._prefetch)

        qs = (
            self
            .select_related(*related)
            .filter(journal=journal)
        )

        return qs

    def year(self, year):
        return(
            self
            .related()
            .filter(year=year)
        )

    def items(self):
        return self.related()


# ----------------------------------------------------------------------------
#                                                                  Income Plan
# ----------------------------------------------------------------------------
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

    objects = YearManager('income_type')

    def __str__(self):
        return f'{self.year}/{self.income_type.title}'

    class Meta:
        ordering = ['income_type']
        unique_together = ('year', 'income_type', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(f'{self.year} metai jau turi {self.income_type.title} planą.')


# ----------------------------------------------------------------------------
#                                                                 Expense Plan
# ----------------------------------------------------------------------------
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

    objects = YearManager('expense_type')

    def __str__(self):
        return f'{self.year}/{self.expense_type.title}'

    class Meta:
        ordering = ['expense_type']
        unique_together = ('year', 'expense_type', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(f'{self.year} metai jau turi {self.expense_type.title} planą.')


# ----------------------------------------------------------------------------
#                                                                  Saving Plan
# ----------------------------------------------------------------------------
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

    objects = YearManager('saving_type')

    def __str__(self):
        return f'{self.year}/{self.saving_type.title}'

    class Meta:
        ordering = ['saving_type']
        unique_together = ('year', 'saving_type', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(f'{self.year} metai jau turi {self.saving_type.title} planą.')


# ----------------------------------------------------------------------------
#                                                                     Day Plan
# ----------------------------------------------------------------------------
class DayPlan(MonthAbstract):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='day_plans'
    )

    objects = YearManager()

    def __str__(self):
        return f'{self.year}'

    class Meta:
        ordering = ['year']
        unique_together = ('year', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(f'{self.year} metai jau turi Dienos planą.')


# ----------------------------------------------------------------------------
#                                                               Necessary Plan
# ----------------------------------------------------------------------------
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

    objects = YearManager()

    def __str__(self):
        return f'{self.year}/{self.title}'

    class Meta:
        ordering = ['year', 'title']
        unique_together = ('year', 'title', 'journal')

    def validate_unique(self, exclude=None):
        try:
            super().validate_unique()
        except ValidationError:
            raise ValidationError(f'{self.year} metai jau turi {self.title} planą.')
