from django.core.validators import MinLengthValidator
from django.db import models

from ..auths.models import User
from ..core.lib import utils


class BooksQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def year(self, year):
        return (
            self
            .related()
            .filter(started__year=year)
        )

    def items(self):
        return self.related()


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
