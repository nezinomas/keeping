from django.db import models
from django.core.validators import MinLengthValidator


class BooksQuerySet(models.QuerySet):
    def year(self, year):
        return self.filter(started__year=year)

    def items(self):
        return self.all()


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

    # objects = BookManager()
    objects = BooksQuerySet.as_manager()

    class Meta:
        ordering = ['-started', 'author']

    def __str__(self):
        return str(self.title)
