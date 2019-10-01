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

    def sum_by_month(self, year, summed_name, month=None, groupby='id'):
        return (
            self
            .annotate(cnt=Count(groupby))
            .values(groupby)
            ._year(year)
            ._month(month)
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{summed_name: Sum('price')})
            .order_by('date')
        )

    def sum_by_day(self, year, month, summed_name, groupby='id'):
        return (
            self
            ._year(year)
            ._month(month)
            .annotate(cnt=Count(groupby))
            .values(groupby)
            .annotate(dt=TruncDay('date'))
            .values('dt')
            .annotate(c=Count('id'))
            .annotate(**{summed_name: Sum('price')})
            .order_by('dt')
        )
