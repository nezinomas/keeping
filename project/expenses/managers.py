from typing import Self

from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.mixins.sum import SumMixin
from ..users.models import User


class ExpenseTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return (
            self.select_related("journal")
            .prefetch_related("expensename_set")
            .filter(journal=user.journal)
        )


class ExpenseNameQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("parent").filter(parent__journal=user.journal)


class ExpenseQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("expense_type", "expense_name", "account").filter(
            expense_type__journal=user.journal
        )
