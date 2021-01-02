from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Count, F, Q
from django.db.models.functions import ExtractYear, TruncYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class BooksQuerySet(SumMixin, models.QuerySet):
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
            .filter(Q(ended__year=year) | Q(ended__isnull=True))
            .filter(started__year__lte=year)
        )

    def items(self):
        return self.related()

    def readed(self, year=None):
        """
        Returns <QuerySet [{'year': int, 'cnt': int}]>
        """
        return (
            self
            .exclude(ended__isnull=True)
            .year_filter(year=year, field='ended')
            .annotate(date=TruncYear('ended'))
            .values('date')
            .annotate(year=ExtractYear(F('date')))
            .annotate(cnt=Count('id'))
            .order_by('year')
            .values('year', 'cnt')
        )

    def reading(self, year):
        """
        Returns {'reading: int}
        """
        return (
            self
            .related()
            .filter(ended__isnull=True)
            .filter(started__year__lte=year)
            .aggregate(reading=Count('id'))
        )


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
