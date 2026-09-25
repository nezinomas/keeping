from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.models import TitleAbstract
from ..journals.models import Journal
from .helpers.models_helper import upload_attachment
from .services.keyword_match import normalise_keyword


class ExpenseType(TitleAbstract):
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="expense_types"
    )
    necessary = models.BooleanField(default=False)

    class Meta:
        unique_together = ["journal", "title"]
        ordering = ["title"]


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

    def __str__(self):
        return f"{(self.date)}/{self.expense_type}/{self.expense_name}"


class ExpenseKeyword(models.Model):
    journal = models.ForeignKey(
        Journal, on_delete=models.CASCADE, related_name="expense_keywords"
    )
    keyword = models.CharField(max_length=100, validators=[MinLengthValidator(3)])
    expense_name = models.ForeignKey(
        ExpenseName, on_delete=models.CASCADE, related_name="expense_keywords"
    )

    class Meta:
        unique_together = ["journal", "keyword"]

    def clean_fields(self, exclude=None):
        # validators and validate_unique must see the stored spelling
        self.keyword = normalise_keyword(self.keyword)
        super().clean_fields(exclude)

    def clean(self):
        if not self.expense_name_id:
            return

        if self.expense_name.parent.journal_id != self.journal_id:
            raise ValidationError(
                {"expense_name": _("The expense name belongs to another journal.")}
            )

    def save(self, *args, **kwargs):
        self.keyword = normalise_keyword(self.keyword)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.keyword
