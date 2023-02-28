from django.db import models
from django.db.models import Q

from ..core.lib import utils


class AccountQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return self.select_related("journal").filter(journal=journal)

    def items(self, year=None):
        year = year or utils.get_user().year
        return self.related().filter(Q(closed__isnull=True) | Q(closed__gte=year))


class AccountBalanceQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        journal = user.journal
        return self.select_related("account").filter(account__journal=journal)

    def items(self):
        return self.related()

    def year(self, year: int):
        return self.items().filter(year=year).order_by("account__title")
