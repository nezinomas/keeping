from django.db.models import Q
from django.db.models.functions import ExtractYear

from ...core.services.model_services import (
    BaseModelService,
    DatedModelService,
    max_year,
)
from .. import models


class AccountModelService(BaseModelService):
    def get_queryset(self):
        return models.Account.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def items(self):
        return self.items_in(self.user.selected_year())

    def items_in(self, year: int):
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))

    def all(self):
        return self.objects.all()

    def none(self):
        return self.objects.none()

    def latest_row_year(self, account: models.Account) -> int:
        if not account.pk:
            return 0

        year = ExtractYear("date")
        return max_year(
            (account.incomes, year),
            (account.expenses, year),
            (account.savings, year),
            (account.savings_close_to, year),
            (account.transactions_from, year),
            (account.transactions_to, year),
            (account.debt_from_account, year),
            (account.debt_return_account, year),
            (account.accounts_worth, year),
        )


class AccountBalanceModelService(DatedModelService):
    def get_queryset(self):
        return models.AccountBalance.objects.select_related("account").filter(
            account__journal=self.user.journal
        )

    def items(self):
        return self.objects.all()

    def year(self, year: int):
        return self.objects.filter(year=year).order_by("account__title")
