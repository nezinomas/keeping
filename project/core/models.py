from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class TitleAbstract(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(
        max_length=100, # Safely expanded!
        blank=False, 
        validators=[
            MinLengthValidator(3),
            RegexValidator(
                regex=r'^[\w \-]+$',
                message=_("Title can only contain letters, numbers, spaces, hyphens, and underscores.")
            )
        ]
    )
    slug = models.SlugField(
        editable=False,
        max_length=100,
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.title)