from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth


class SumMixin():
    def sum_by_month(self, year, summed_col_name):
        return (
            self
            .annotate(tmp=Count('id'))
            .values('tmp')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(**{summed_col_name: Sum('price')})
            .filter(date__year=year)
            .values('date', summed_col_name)
            .order_by('date')
        )
