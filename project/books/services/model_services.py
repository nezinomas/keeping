from django.db.models import Count, F, Q
from django.db.models.functions import ExtractYear, TruncYear

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models


class BookModelService(SumMixin, BaseModelService):
    def get_queryset(self):
        return models.Book.objects.select_related("user").filter(user=self.user)

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
        qs = self.year_filter(self.objects, year=year, field="ended")

        return (
            qs.exclude(ended__isnull=True)
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


class BookTargetModelService(BaseModelService):
    def get_queryset(self):
        return models.BookTarget.objects.select_related("user").filter(user=self.user)

    def year(self, year):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects
