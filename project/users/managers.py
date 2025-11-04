from typing import Optional

from django.contrib.auth.models import UserManager

from ..core.lib import utils


class KeepingUserManager(UserManager):
    def related(self, user = None):
        #Todo: Refactore user
        try:
            journal = user.journal
        except AttributeError:
            print("Getting journal from utils.get_user() in exception")
            journal = utils.get_user().journal

        return self.select_related("journal").filter(journal=journal)
