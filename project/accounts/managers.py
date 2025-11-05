from django.db import models

from ..users.models import User


class AccountQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)


class AccountBalanceQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("account").filter(account__journal=user.journal)
