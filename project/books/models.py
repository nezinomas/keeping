from django.core.validators import (MaxValueValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import models

from ..users.models import User
from .managers import BooksQuerySet, BookTargetQuerySet


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
        validators=[MinLengthValidator(2)]
    )
    remark = models.TextField(
        max_length=200,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='books'
    )

    # objects = BookManager()
    objects = BooksQuerySet.as_manager()

    class Meta:
        ordering = ['-started', 'author']

    def __str__(self):
        return str(self.title)


class BookTarget(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='book_targets'
    )

    objects = BookTargetQuerySet.as_manager()

    def __str__(self):
        return f'{self.year}: {self.quantity}'

    class Meta:
        ordering = ['-year']
        unique_together = ['year', 'user']
