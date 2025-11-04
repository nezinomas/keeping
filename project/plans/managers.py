from typing import Optional

from django.db import models

from ..core.lib import utils
from ..users.models import User


class YearManager(models.Manager):
    def __init__(self, prefetch=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefetch = prefetch

    def related(self, user: Optional[User] = None):
        #Todo: Refactore user
        try:
            journal = user.journal
        except AttributeError:
            print("Getting journal from utils.get_user() in exception")
            journal = utils.get_user().journal
        related = ["journal"]

        if self._prefetch:
            related.append(self._prefetch)

        return self.select_related(*related).filter(journal=journal)

    def year(self, year):
        return self.related().filter(year=year)

    def items(self):
        return self.related()
