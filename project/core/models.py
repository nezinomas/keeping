from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class TitleAbstract(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(
        max_length=25,
        blank=False,
        validators=[MinLengthValidator(3)]
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


class MonthAbstract(models.Model):
    class Meta:
        abstract = True

    january = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    february = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    march = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    april = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    may = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    june = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    july = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    august = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    september = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    october = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    november = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    december = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
