from typing import cast

from django.db.models import Count, F, Q
from django.db.models.functions import ExtractYear, TruncYear

from ...core.services.model_services import BaseModelService
from .. import managers, models


class BookModelService(BaseModelService[managers.BooksQuerySet]):
    def get_queryset(self):
        return cast(managers.BooksQuerySet, models.Book.objects).related(self.user)

    def year(self, year):
        return self.objects.filter(Q(ended__year=year) | Q(ended__isnull=True)).filter(
            started__year__lte=year
        )

    def items(self):
        return self.objects

    def readed(self, year=None):
        """
        Returns <QuerySet [{'year': int, 'cnt': int}]>
        """
        return (
            self.objects.exclude(ended__isnull=True)
            .year_filter(year=year, field="ended")
            .annotate(date=TruncYear("ended"))
            .values("date")
            .annotate(year=ExtractYear(F("date")))
            .annotate(cnt=Count("id"))
            .order_by("year")
            .values("year", "cnt")
        )

    def reading(self, year):
        """
        Returns {'reading: int}
        """
        return (
            self.objects.filter(ended__isnull=True)
            .filter(started__year__lte=year)
            .aggregate(reading=Count("id"))
        )


class BookTargetModelService(BaseModelService[managers.BookTargetQuerySet]):
    def get_queryset(self):
        return cast(managers.BookTargetQuerySet, models.BookTarget.objects).related(
            self.user
        )

    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects
