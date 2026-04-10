from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _

from ..expenses.models import ExpenseType
from ..incomes.models import IncomeType
from ..journals.models import Journal
from ..savings.models import SavingType


class IncomePlan(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    month = models.PositiveIntegerField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)
    income_type = models.ForeignKey(IncomeType, on_delete=models.CASCADE)
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="income_plans"
    )

    def __str__(self):
        return f"{self.year}/{self.income_type.title}"

    class Meta:
        ordering = ["income_type"]
        unique_together = ("year", "month", "income_type", "journal")


class ExpensePlan(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    month = models.PositiveIntegerField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.CASCADE)
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="expense_plans"
    )

    def __str__(self):
        return f"{self.year}/{self.expense_type.title}"

    class Meta:
        ordering = ["expense_type"]
        unique_together = ("year", "month", "expense_type", "journal")


class SavingPlan(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    month = models.PositiveIntegerField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)
    saving_type = models.ForeignKey(SavingType, on_delete=models.CASCADE)
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="saving_plans"
    )

    def __str__(self):
        return f"{self.year}/{self.saving_type.title}"

    class Meta:
        ordering = ["saving_type"]
        unique_together = ("year", "month", "saving_type", "journal")


class DayPlan(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    month = models.PositiveIntegerField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="day_plans"
    )

    def __str__(self):
        return f"{self.year}"

    class Meta:
        ordering = ["year"]
        unique_together = ("year", "month", "journal")


class NecessaryPlan(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    month = models.PositiveIntegerField(null=True, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=100)
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.CASCADE)
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="necessary_plans"
    )

    def __str__(self):
        return f"{self.year}/{self.title}"

    class Meta:
        ordering = ["year", "month", "expense_type", "title"]
        unique_together = ("year", "month", "title", "expense_type", "journal")
