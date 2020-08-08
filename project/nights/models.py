from django.db import models

from ..counters.models import Counter, CounterQuerySet
from .apps import App_name as NightsAppName


class NightQuerySet(CounterQuerySet, models.QuerySet):
    App_name = NightsAppName


class Night(Counter):
    objects = NightQuerySet.as_manager()

    class Meta:
        proxy = True
