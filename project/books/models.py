from django.core.validators import (MaxValueValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import models
from django.urls import reverse_lazy

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

    objects = BooksQuerySet.as_manager()

    class Meta:
        ordering = ['-started', 'author']

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse_lazy("books:books_update", kwargs={"pk": self.pk})


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

    class Meta:
        ordering = ['-year']
        unique_together = ['year', 'user']

    def __str__(self):
        return f'{self.year}: {self.quantity}'

    def get_absolute_url(self):
        return reverse_lazy("books:books_target_update", kwargs={"pk": self.pk})
