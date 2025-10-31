from django.db import models
from django.db.models import Q

# from ..core.lib import utils
from ..users.models import User


class AccountQuerySet(models.QuerySet):
    def related(self, user: User):
        # journal = utils.get_user().journal
        return self.select_related("journal").filter(journal=user.journal)

    def items(self, user: User, year=None):
        year = year or user.year
        return self.related(user).filter(Q(closed__isnull=True) | Q(closed__gte=year))


class AccountBalanceQuerySet(models.QuerySet):
    def related(self, user: User):
        # user = utils.get_user()
        # journal = user.journal
        return self.select_related("account").filter(account__journal=user.journal)

    def items(self, user: User):
        return self.related(user)

    def year(self, user: User, year: int):
        return self.items(user).filter(year=year).order_by("account__title")
