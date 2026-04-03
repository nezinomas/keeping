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
            qs
            .annotate(cnt=Count(groupby), y=TruncYear("date"))
            .values("cnt", "y")
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by("y")
            .values(sum_annotation, year=ExtractYear(F("y")))
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
            qs
            .annotate(grouped_by=Count(groupby), month=TruncMonth("date"))
            .values("grouped_by", "month")
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by("month")
            .values(sum_annotation, date=F("month"))
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
            qs
            .annotate(grouped_by=Count(groupby), day=TruncDay("date"))
            .values("grouped_by", "day")
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by("day")
            .values(sum_annotation, date=F("day"))
        )
