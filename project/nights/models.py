from django.db import models

from ..counters.models import Counter, CounterQuerySet
from .apps import App_name as app_name


class NightQuerySet(CounterQuerySet, models.QuerySet):
    App_name = app_name


class Night(Counter):
    objects = NightQuerySet.as_manager()

    class Meta:
        proxy = True
