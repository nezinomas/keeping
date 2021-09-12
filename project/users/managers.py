
from django.contrib.auth.models import UserManager

from ..core.lib import utils


class KeepingUserManager(UserManager):
    def related(self):
        journal = utils.get_user().journal

        return (
            self
            .select_related('journal')
            .filter(journal=journal)
        )
