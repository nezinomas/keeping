from typing import cast

from django.db.models import Value

from ...users.models import User
from .. import managers, models


class CommonMethodsMixin:
    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects


class TransactionModelService(CommonMethodsMixin):
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.TransactionQuerySet, models.Transaction.objects
        ).related(user)


class SavingCloseModelService(CommonMethodsMixin):
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.SavingCloseQuerySet, models.SavingClose.objects
        ).related(user)

    def sum_by_month(self, year, month=None):
        return self.objects.month_sum(year=year, month=month).annotate(
            title=Value("savings_close")
        )


class SavingChangeModelService(CommonMethodsMixin):
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.SavingChangeQuerySet, models.SavingChange.objects
        ).related(user)
