from django.db import models
from django.core.validators import MinLengthValidator


class BookManager(models.Manager):
    def items(self, year):
        return self.get_queryset().filter(started__year=year)


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
