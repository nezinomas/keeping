from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth, TruncDay


class SumMixin():
    def _year(self, year):
        return self.filter(date__year=year)

    def _month(self, month):
        if month:
            return self.filter(date__month=month)
        else:
            return self

    def month_sum(self,
                  year,
                  summed_name,
                  month=None,
                  groupby='id',
                  sum_column_name='price'):
        return (
            self
            ._year(year)
            ._month(month)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{summed_name: Sum(sum_column_name)})
            .order_by('date')
        )

    def sum_by_day(self, year, month, summed_name):
        return (
            self
            ._year(year)
            ._month(month)
            .annotate(c=Count('id'))
            .values('c')
            .annotate(date=TruncDay('date'))
            .annotate(**{summed_name: Sum('price')})
            .order_by('date')
        )
