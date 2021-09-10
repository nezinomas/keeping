from django.db import models
from django.utils.text import slugify
from project.core.models import TitleAbstract

from ..counters.managers import CounterQuerySet
from ..counters.models import Counter
from ..users.models import User
from .managers import CountTypeQuerySet


class CountQuerySet(CounterQuerySet, models.QuerySet):
    # App_name = app_name
    pass


class Count(Counter):
    objects = CountQuerySet.as_manager()

    class Meta:
        proxy = True


class CountType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = CountTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['user', 'title']
        ordering = ['title']

    def __str__(self):
        return self.title

    __original_title = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.__original_title = self.title

    def save(self, *args, **kwargs):
        if self.pk:
            if self.title != self.__original_title:
                (Count
                 .objects
                 .related()
                 .filter(counter_type=slugify(self.__original_title))
                 .update(counter_type=slugify(self.title)))

        super().save(*args, **kwargs)

        self.__original_title = self.title

    def delete(self, *args, **kwargs):
        (Count
         .objects
         .related()
         .filter(counter_type=slugify(self.title))
         .delete())

        super().delete(*args, **kwargs)
