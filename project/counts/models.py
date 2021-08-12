from django.db import models
from project.core.models import TitleAbstract

from ..counters.managers import CounterQuerySet
from ..counters.models import Counter
from ..users.models import User
from .apps import App_name as app_name


class CountQuerySet(CounterQuerySet, models.QuerySet):
    App_name = app_name


class Count(Counter):
    objects = CountQuerySet.as_manager()

    class Meta:
        proxy = True


class CountType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ['user', 'title']
        ordering = ['title']
