from django.db import models
from django.contrib.auth.models import UserManager


class KeepingUserManager(UserManager):
    def related(self):
        return (
            self
            .select_related('journal')
        )

