from datetime import date

from django.db.models import F, Max, Sum
from django.db.models.functions import TruncMonth


class SpanReadsMixin:
    """Reads of a dated model service over a span; the caller gives the bounds."""

    def sum_by_between(self, field: str, start: date, end: date):
        # the explicit order_by: Meta.ordering on a foreign key JOINs into the sum
        return (
            self.objects.filter(date__range=(start, end))
            .values(field)
            .annotate(sum=Sum("price"), title=F(f"{field}__title"), pk=F(f"{field}_id"))
            .order_by("-sum", "title")
            .values("pk", "title", "sum")
        )

    def sum_by_month_between(self, start: date, end: date):
        return (
            self.objects.filter(date__range=(start, end))
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(sum=Sum("price"))
            .order_by("month")
            .values("sum", date=F("month"))
        )

    def last_date_by(self, field: str, end: date):
        return (
            self.objects.filter(date__lte=end)
            .values(field)
            .annotate(date=Max("date"), title=F(f"{field}__title"), pk=F(f"{field}_id"))
            .order_by()
            .values("pk", "title", "date")
        )
