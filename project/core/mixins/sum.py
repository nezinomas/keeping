from django.db.models import Count, F, Sum
from django.db.models.functions import ExtractYear, TruncDay, TruncMonth, TruncYear


class SumMixin:
    def year_filter(self, qs, year, field="date"):
        return qs.filter(**{f"{field}__year": year}) if year else qs

    def month_filter(self, qs, month, field="date"):
        return qs.filter(**{f"{field}__month": month}) if month else qs

    def year_sum(
        self, qs, year=None, sum_annotation="sum", groupby="id", sum_column="price"
    ):
        qs = self.year_filter(qs, year)
        return (
            qs.annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncYear("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by("date")
            .annotate(year=ExtractYear(F("date")))
            .values("year", sum_annotation)
        )

    def month_sum(
        self,
        qs,
        year,
        month=None,
        sum_annotation="sum",
        sum_column="price",
        groupby="id",
    ):
        qs = self.year_filter(qs, year)
        qs = self.month_filter(qs, month)
        return (
            qs.annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by("date")
            .values("date", sum_annotation)
        )

    def day_sum(
        self,
        qs,
        year,
        month=None,
        sum_annotation="sum",
        sum_column="price",
        groupby="id",
    ):
        qs = self.year_filter(qs, year)
        qs = self.month_filter(qs, month)
        return (
            qs.annotate(c=Count(groupby))
            .values("c")
            .annotate(date=TruncDay("date"))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by("date")
            .values("date", sum_annotation)
        )
