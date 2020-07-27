from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear


class SumMixin():
    def _year(self, year):
        if year:
            return self.filter(date__year=year)

        return self

    def _month(self, month):
        if month:
            return self.filter(date__month=month)

        return self

    def year_sum(self,
                 year,
                 sum_annotation,
                 groupby='id',
                 sum_column='price'):
        return (
            self
            ._year(year)
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
                  sum_annotation,
                  month=None,
                  groupby='id',
                  sum_column='price'):
        return (
            self
            ._year(year)
            ._month(month)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{sum_annotation: Sum(sum_column)})
            .order_by('date')
        )

    def day_sum(self, year, month, sum_annotation):
        return (
            self
            ._year(year)
            ._month(month)
            .annotate(c=Count('id'))
            .values('c')
            .annotate(date=TruncDay('date'))
            .annotate(**{sum_annotation: Sum('price')})
            .order_by('date')
        )
