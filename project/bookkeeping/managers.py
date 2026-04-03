from django.db import models

from ..users.models import User


class AccountWorthQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("account").filter(account__journal=user.journal)




class SavingWorthQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("saving_type").filter(
            saving_type__journal=user.journal
        )


class PensionWorthQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("pension_type").filter(
            pension_type__journal=user.journal
        )
