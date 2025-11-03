from typing import Optional

from django.contrib.auth.models import UserManager

from ..core.lib import utils
from ..journals.models import Journal


class KeepingUserManager(UserManager):
    def related(self, journal: Optional[Journal] = None):
        #Todo: Refactore Journal
        journal = journal or utils.get_user().journal

        return self.select_related("journal").filter(journal=journal)
