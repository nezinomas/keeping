from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear


class SumMixin():
    def year_filter(self, year):
        if year:
            return self.filter(date__year=year)

        return self
    year_filter.queryset_only = True

    def month_filter(self, month):
        if month:
            return self.filter(date__month=month)

        return self
    month_filter.queryset_only = True

    def year_sum(self,
                 year,
                 sum_annotation,
                 groupby='id',
                 sum_column='price'):
        return (
            self
            .year_filter(year)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncYear('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
        )

    def month_sum(self,
                  year,
                  month=None,
                  sum_annotation='sum',
                  sum_column='price',
                  groupby='id'):
        return (
            self
            .year_filter(year)
            .month_filter(month)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
        )

    def day_sum(self,
                year,
                month=None,
                sum_annotation='sum',
                sum_column='price',
                groupby='id'):
        return (
            self
            .year_filter(year)
            .month_filter(month)
            .annotate(c=Count(groupby))
            .values('c')
            .annotate(date=TruncDay('date'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
        )
