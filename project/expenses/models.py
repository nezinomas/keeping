from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.urls import reverse_lazy

from ..accounts.models import Account
from ..core.lib import utils
from ..core.models import TitleAbstract
from ..journals.models import Journal
from .helpers.models_helper import upload_attachment
from .managers import ExpenseNameQuerySet, ExpenseQuerySet, ExpenseTypeQuerySet


class ExpenseType(TitleAbstract):
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="expense_types"
    )
    necessary = models.BooleanField(default=False)

    # Managers
    objects = ExpenseTypeQuerySet.as_manager()

    class Meta:
        unique_together = ["journal", "title"]
        ordering = ["title"]

    def get_absolute_url(self):
        return reverse_lazy("expenses:type_update", kwargs={"pk": self.pk})


class ExpenseName(TitleAbstract):
    title = models.CharField(
        max_length=254, blank=False, validators=[MinLengthValidator(3)]
    )
    valid_for = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(ExpenseType, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("title", "parent")
        ordering = [F("valid_for").desc(nulls_first=True), "title"]

    # Managers
    objects = ExpenseNameQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse_lazy("expenses:name_update", kwargs={"pk": self.pk})


class Expense(models.Model):
    date = models.DateField()
    price = models.PositiveIntegerField()
    quantity = models.IntegerField(
        default=1,
    )
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.CASCADE)
    expense_name = models.ForeignKey(ExpenseName, on_delete=models.CASCADE)
    remark = models.TextField(max_length=1000, blank=True)
    exception = models.BooleanField(default=False)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="expenses"
    )
    attachment = models.ImageField(
        blank=True,
        upload_to=upload_attachment,
    )

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["expense_type"]),
            models.Index(fields=["expense_name"]),
        ]

    # Managers
    objects = ExpenseQuerySet.as_manager()

    def __str__(self):
        return f"{(self.date)}/{self.expense_type}/{self.expense_name}"

    def get_absolute_url(self):
        return reverse_lazy("expenses:update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("expenses:delete", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # update first journal record
        user = utils.get_user()
        journal = Journal.objects.get(pk=user.journal.pk)

        if journal.first_record > self.date:
            journal.first_record = self.date
            journal.save()
