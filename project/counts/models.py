from django.db import models

from ..counters.managers import CounterQuerySet
from ..counters.models import Counter
from .apps import App_name as app_name


class CountQuerySet(CounterQuerySet, models.QuerySet):
    App_name = app_name


class Count(Counter):
    objects = CountQuerySet.as_manager()

    class Meta:
        proxy = True
