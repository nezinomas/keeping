from django.db import models

from ..core.models import TitleAbstract


class Account(TitleAbstract):
    class Meta:
        ordering = ['title']
