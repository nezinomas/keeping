from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .validators import validate_title_characters, validate_title_slug


class TitleAbstract(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(
        max_length=100,
        blank=False,
        validators=[
            MinLengthValidator(3),
            validate_title_characters,
            validate_title_slug,
        ],
    )
    slug = models.SlugField(
        editable=False,
        max_length=100,
    )

    def clean(self):
        super().clean()
        owner_filter = self._owner_filter()
        if not owner_filter:
            return

        taken = (
            type(self)
            .objects.filter(slug=slugify(self.title), **owner_filter)
            .exclude(pk=self.pk)
            .first()
        )
        # compared in Python: MariaDB's collation would match Būstas to Bustas
        if not taken or taken.title == self.title:
            return

        raise ValidationError(
            {
                "title": ValidationError(
                    _("Title is too close to “%(title)s”, which already exists."),
                    code="slug_taken",
                    params={"title": taken.title},
                )
            }
        )

    def _owner_filter(self):
        for fields in self._meta.unique_together:
            if "title" in fields:
                attnames = [
                    self._meta.get_field(name).attname
                    for name in fields
                    if name != "title"
                ]
                return {attname: getattr(self, attname) for attname in attnames}
        return {}

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)
