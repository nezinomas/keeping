from django.db.models import Count, IntegerField, Sum
from django.db.models.functions import Cast, ExtractMonth, TruncMonth


class SumMixin():
    def sum_by_month(self, year, summed_col_name):
        return (
            self
            .annotate(_month=TruncMonth('date'))
            .values('_month')
            .annotate(c=Count('id'))
            .annotate(**{summed_col_name: Sum('price')})
            .annotate(month=Cast(ExtractMonth('_month'), IntegerField()))
            .filter(_month__year=year)
            .values('month', 'incomes')
            .order_by('_month')
        )
