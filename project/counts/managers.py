from django.db import models

from ..core.lib import utils


class CountTypeQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()

        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def items(self):
        return self.related()
