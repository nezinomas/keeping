from django.contrib.auth.models import UserManager


class KeepingUserManager(UserManager):
    def related(self, user):
        return self.select_related("journal").filter(journal=user.journal)
