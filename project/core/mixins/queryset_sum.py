from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


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
