from django.db import models
from django.utils.translation import gettext as _

from ..core.lib import utils


class YearManager(models.Manager):
    def __init__(self, prefetch=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefetch = prefetch

    def related(self):
        journal = utils.get_user().journal
        related = ['journal']

        if self._prefetch:
            related.append(self._prefetch)

        qs = (
            self
            .select_related(*related)
            .filter(journal=journal)
        )

        return qs

    def year(self, year):
        return(
            self
            .related()
            .filter(year=year)
        )

    def items(self):
        return self.related()
