
import os

from django.conf import settings
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.text import slugify
from project.core.models import TitleAbstract

from ..core.lib import utils
from ..users.models import User
from .managers import CountQuerySet, CountTypeQuerySet


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _generate_counts_menu()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        _generate_counts_menu()

    def get_absolute_url(self):
        slug = utils.get_request_kwargs('slug')
        return (
            reverse_lazy(
                'counts:type_update',
                kwargs={'slug': slug})
        )

    def get_delete_url(self):
        slug = utils.get_request_kwargs('slug')
        return (
            reverse_lazy(
                'counts:type_delete',
                kwargs={'slug': slug})
        )


class Count(models.Model):
    date = models.DateField()
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)]
    )
    count_type = models.ForeignKey(
        CountType,
        on_delete=models.CASCADE,
        related_name='counts'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = CountQuerySet.as_manager()

    def __str__(self):
        return f'{self.date}: {self.quantity}'

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']

    def get_absolute_url(self):
        return reverse_lazy("counts:update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("counts:delete", kwargs={"pk": self.pk})


def _generate_counts_menu():
    journal = utils.get_user().journal
    qs = CountType.objects.related()

    if qs:
        journal_pk = str(journal.pk)
        folder = os.path.join(settings.MEDIA_ROOT, journal_pk)
        file = os.path.join(folder, 'menu.html')

        if not os.path.isdir(folder):
            os.mkdir(folder)

        content = render_to_string(
            template_name='counts/menu.html',
            context={'slugs': qs},
            request=None
        )

        with open(file, 'w+') as f:
            f.write(content)
