from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


class SumMixin():
    def sum_by_month(self, year, summed_name='sum', groupby='id'):
        return (
            self
            .annotate(tmp=Count(groupby))
            .values(groupby)
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{summed_name: Sum('price')})
            .filter(date__year=year)
            .values('date', summed_name)
            .order_by('date')
        )
