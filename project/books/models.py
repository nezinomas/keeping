from django.db import models
from django.core.validators import MinLengthValidator


class BookManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = self.get_queryset()

        if 'year' in kwargs:
            year = kwargs['year']
            qs = qs.filter(started__year=year)

        return qs


class Book(models.Model):
    started = models.DateField()
    ended = models.DateField(
        null=True,
        blank=True
    )
    author = models.CharField(
        max_length=254,
        validators=[MinLengthValidator(3)]
    )
    title = models.CharField(
        max_length=254,
        validators=[MinLengthValidator(3)]
    )

    objects = BookManager()

    class Meta:
        ordering = ['-started', 'author']

    def __str__(self):
        return str(self.title)
