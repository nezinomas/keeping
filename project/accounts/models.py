from django.db import models

from ..core.models import TitleAbstract


class AccountManager(models.Manager):
    def items(self, *args, **kwargs):
        return self.get_queryset()


class Account(TitleAbstract):
    objects = AccountManager()

    class Meta:
        ordering = ['title']
