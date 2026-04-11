from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.text import slugify


class TitleAbstract(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(
        max_length=25, blank=False, validators=[MinLengthValidator(3)]
    )
    slug = models.SlugField(
        editable=False,
        max_length=25,
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)